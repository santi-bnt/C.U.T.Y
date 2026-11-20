# Board interface

`cuty_board.h` is the only path from the tasks to hardware: output stage, kill switch,
battery, watchdog, UART TX ring, LED and boot info. It has three implementations: the
Black Pill (`Core/Src/board_f401.c`), the POSIX simulator (`sim/board_sim.c`) and the
host test doubles (`tests/test_rtos.c`).
