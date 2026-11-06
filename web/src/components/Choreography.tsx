import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { chapterIds } from "../viewer/choreography";
import type { StoryMotion } from "../viewer/storyMotion";
gsap.registerPlugin(ScrollTrigger);

export default function Choreography({ motion }: { motion: StoryMotion }) {
  useEffect(() => {
    let timeline: gsap.core.Timeline | undefined;
    let frame = 0;
    const cursor = { value: 0 };
    const build = () => {
      timeline?.scrollTrigger?.kill();
      timeline?.kill();
      cursor.value = 0;
      timeline = gsap.timeline({
        defaults: { ease: "none" },
        onUpdate: () => motion.setProgress(cursor.value),
        scrollTrigger: {
          start: 0,
          end: () => ScrollTrigger.maxScroll(window),
          scrub: 0.45,
        },
      });
      let lastEnd = 0;
      chapterIds.slice(1).forEach((id, index) => {
        const element = document.getElementById(id);
        if (!element) return;
        const top = element.getBoundingClientRect().top + window.scrollY;
        const start = Math.max(lastEnd, top - window.innerHeight * 0.9);
        const end = Math.max(start + 1, top - window.innerHeight * 0.15);
        timeline!.fromTo(
          cursor,
          { value: index },
          { value: index + 1, duration: end - start, immediateRender: false },
          start,
        );
        lastEnd = end;
      });
      timeline.to(
        cursor,
        {
          value: chapterIds.length - 1,
          duration: Math.max(1, ScrollTrigger.maxScroll(window) - lastEnd),
        },
        lastEnd,
      );
      timeline.scrollTrigger?.refresh();
      timeline.scrollTrigger?.update();
      motion.setProgress(cursor.value);
    };
    const schedule = () => {
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(build);
    };
    build();
    const anchor = document.getElementById(
      decodeURIComponent(window.location.hash.slice(1)),
    );
    if (anchor) {
      let parent = anchor.parentElement;
      while (parent) {
        if (parent instanceof HTMLDetailsElement) parent.open = true;
        parent = parent.parentElement;
      }
      frame = requestAnimationFrame(() => {
        anchor.scrollIntoView({ behavior: "instant", block: "start" });
        schedule();
      });
    }
    const observer = new ResizeObserver(schedule);
    const main = document.querySelector("main");
    if (main) observer.observe(main);
    window.addEventListener("resize", schedule);
    const move = (event: PointerEvent) => {
      if (
        event.pointerType !== "mouse" ||
        window.matchMedia("(prefers-reduced-motion: reduce)").matches
      )
        return;
      motion.move(
        (event.clientX / window.innerWidth) * 2 - 1,
        (event.clientY / window.innerHeight) * 2 - 1,
      );
    };
    window.addEventListener("pointermove", move, { passive: true });
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("resize", schedule);
      window.removeEventListener("pointermove", move);
      timeline?.scrollTrigger?.kill();
      timeline?.kill();
    };
  }, [motion]);
  useEffect(() => {
    const context = gsap.context(() => {
      if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      gsap.fromTo(
        ".hero-letter",
        { yPercent: 110 },
        {
          yPercent: 0,
          stagger: 0.035,
          duration: 1.15,
          ease: "power4.out",
          clearProps: "transform",
        },
      );
      gsap.utils
        .toArray<HTMLElement>(".reveal-line > span")
        .forEach((element) => {
          gsap.fromTo(
            element,
            { yPercent: 115 },
            {
              yPercent: 0,
              duration: 0.9,
              ease: "power3.out",
              scrollTrigger: {
                trigger: element.parentElement,
                start: "top 95%",
                once: true,
              },
              clearProps: "transform",
            },
          );
        });
    });
    return () => context.revert();
  }, []);
  return null;
}
