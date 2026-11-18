#include "../App/control/body_control.h"
#include "../App/servos/servo.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
static CutyController make(CutyLossPolicy policy) {
    CutyController c; CutyLimits limits[CUTY_AXES];
    for (unsigned i=0;i<CUTY_AXES;++i) limits[i]=(CutyLimits){-1,1,0.8f,1.5f};
    assert(cuty_control_init(&c,limits,500,policy)); return c;
}
static bool send(CutyController *c,const char *s,uint32_t now) {
    CutyCommand cmd; assert(cuty_parse_line(s,&cmd)); return cuty_control_command(c,&cmd,now);
}
static void arm(CutyController *c,uint32_t now) {
    assert(send(c,"V1,HB",now)); assert(send(c,"V1,ARM",now));
    assert(c->safety.state==CUTY_READY); assert(send(c,"V1,START",now));
}
int main(void) {
    CutyParser p={0}; CutyCommand cmd;
    const char *valid="V1,TARGET,0,350\r\n";
    for (size_t i=0;i<strlen(valid);++i)
        assert(cuty_rx_byte(&p,(uint8_t)valid[i],&cmd)==(i==strlen(valid)-1?CUTY_RX_COMMAND:CUTY_RX_NONE));
    assert(cmd.axis==0 && fabs(cmd.target-0.35f)<1e-6f);
    const char *bad[]={"V1,TARGET,5,0","V1,TARGET,0,nan","V1,TARGET,0,1001","V1,TARGET,0,1x",
        "V1,TARGET,0,","V1,TARGET,0,+5","V1,TARGET,0,1,2","SET_HEAD,15,-4","V1,HB ","V1,TARGET,0,999999999999"};
    for(unsigned i=0;i<sizeof(bad)/sizeof(bad[0]);++i) assert(!cuty_parse_line(bad[i],&cmd));
    for(unsigned i=0;i<100;++i) cuty_rx_byte(&p,'A',&cmd);
    assert(cuty_rx_byte(&p,'\n',&cmd)==CUTY_RX_ERROR);
    cuty_rx_byte(&p,0,&cmd); assert(cuty_rx_byte(&p,'\n',&cmd)==CUTY_RX_ERROR);
    const char *hb="V1,HB\n";
    for(size_t i=0;i<strlen(hb);++i) cuty_rx_byte(&p,(uint8_t)hb[i],&cmd);
    assert(cmd.kind==CUTY_HEARTBEAT);
    CutyController c=make(CUTY_FREEZE_COMMAND);
    assert(c.safety.state==CUTY_DISARMED && !cuty_control_output_requested(&c));
    assert(!send(&c,"V1,ARM",0)); arm(&c,0);
    assert(send(&c,"V1,TARGET,0,350",0));
    assert(send(&c,"V1,TARGET,0,-500",0)); /* latest goal wins in core */
    assert(c.axes[0].target==-0.5f);
    for(uint32_t now=20;now<=8000;now+=20) {
        assert(send(&c,"V1,HB",now)); float old=c.axes[0].velocity;
        cuty_control_tick(&c,now,0.02f);
        assert(c.safety.state==CUTY_ACTIVE);
        if (fabs(c.axes[0].velocity-old)>1.5f*0.02f+1e-6f)
            printf("trajectory delta: t=%u old=%f new=%f delta=%f\n",now,(double)old,(double)c.axes[0].velocity,fabs(c.axes[0].velocity-old));
        assert(fabs(c.axes[0].velocity)<=0.80001f);
        assert(fabs(c.axes[0].velocity-old)<=1.5f*0.02f+1e-6f);
        assert(c.axes[0].commanded>=-1 && c.axes[0].commanded<=1);
    }
    assert(fabs(c.axes[0].commanded+0.5f)<0.001f);
    float before=c.axes[0].commanded;
    cuty_control_tick(&c,8500,0.02f);
    assert(c.safety.state==CUTY_FAULT && c.axes[0].commanded==before);
    assert(cuty_control_output_requested(&c));
    assert(send(&c,"V1,DISARM",8500));
    assert(c.safety.state==CUTY_FAULT && !cuty_control_output_requested(&c));
    assert(send(&c,"V1,HB",8501)); assert(c.safety.state==CUTY_FAULT);
    assert(!send(&c,"V1,START",8501));
    assert(send(&c,"V1,RESET",8502)); assert(!send(&c,"V1,ARM",8502));
    arm(&c,8503); assert(send(&c,"V1,TARGET,0,1000",8503));
    assert(send(&c,"V1,DISARM",8504)); assert(!cuty_control_output_requested(&c));
    arm(&c,8505); cmd=(CutyCommand){CUTY_TARGET,5,0}; assert(!cuty_control_command(&c,&cmd,8505));
    assert(c.safety.state==CUTY_FAULT);
    c=make(CUTY_RELEASE_OUTPUT); arm(&c,UINT32_MAX-100);
    cuty_control_tick(&c,398,0.02f); assert(c.safety.state==CUTY_ACTIVE);
    cuty_control_tick(&c,399,0.02f); assert(c.safety.state==CUTY_FAULT && !cuty_control_output_requested(&c));
    c=make(CUTY_RELEASE_OUTPUT); arm(&c,0); cuty_control_tick(&c,20,NAN); assert(c.safety.state==CUTY_FAULT);
    c=make(CUTY_FREEZE_COMMAND);
    assert(send(&c,"V1,HB",0)); assert(send(&c,"V1,ARM",0));
    cuty_control_tick(&c,500,0.02f);
    assert(c.safety.state==CUTY_FAULT && !cuty_control_output_requested(&c));
    uint16_t pulse; assert(cuty_servo_pulse(0,1000,2000,&pulse)&&pulse==1500);
    assert(!cuty_servo_pulse(NAN,1000,2000,&pulse)); assert(!cuty_servo_pulse(2,1000,2000,&pulse));
    printf("PASS: framing, parsing, limits, trajectory, states, heartbeat, rollover, pulse conversion\n");
    return 0;
}
