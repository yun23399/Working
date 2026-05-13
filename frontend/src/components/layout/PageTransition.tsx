import { motion, useReducedMotion } from 'framer-motion'
import type { ReactNode } from 'react'

interface PageTransitionProps {
  children: ReactNode
}

// 页面转场容器，为不同路由页面提供统一的进入与离开动效
export function PageTransition({ children }: PageTransitionProps) {
  const prefersReducedMotion = useReducedMotion()

  const contentInitial = prefersReducedMotion
    ? { opacity: 0 }
    : { opacity: 0, y: 22, scale: 0.992, filter: 'blur(8px)' }
  const contentAnimate = prefersReducedMotion
    ? {
        opacity: 1,
        transition: { duration: 0.18, ease: 'easeOut' },
      }
    : {
        opacity: 1,
        y: 0,
        scale: 1,
        filter: 'blur(0px)',
        transition: { duration: 0.32, ease: [0.22, 1, 0.36, 1] },
      }
  const contentExit = prefersReducedMotion
    ? {
        opacity: 0,
        transition: { duration: 0.12, ease: 'easeIn' },
      }
    : {
        opacity: 0,
        y: -16,
        scale: 0.996,
        filter: 'blur(6px)',
        transition: { duration: 0.18, ease: [0.4, 0, 1, 1] },
      }

  const glowInitial = prefersReducedMotion
    ? { opacity: 0 }
    : { opacity: 0, scale: 0.94, x: -18, y: -20 }
  const glowAnimate = prefersReducedMotion
    ? {
        opacity: 0.4,
        transition: { duration: 0.16, ease: 'easeOut' },
      }
    : {
        opacity: 0.9,
        scale: 1,
        x: 0,
        y: 0,
        transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] },
      }
  const glowExit = prefersReducedMotion
    ? {
        opacity: 0,
        transition: { duration: 0.1, ease: 'easeIn' },
      }
    : {
        opacity: 0,
        scale: 1.04,
        x: 14,
        y: -12,
        transition: { duration: 0.18, ease: [0.4, 0, 1, 1] },
      }

  return (
    <motion.div
      initial={contentInitial}
      animate={contentAnimate}
      exit={contentExit}
      className="relative min-h-screen overflow-hidden"
    >
      <motion.div
        aria-hidden
        initial={glowInitial}
        animate={glowAnimate}
        exit={glowExit}
        className="pointer-events-none absolute inset-x-0 top-0 h-48 bg-[radial-gradient(circle_at_top,rgba(95,124,255,0.18),transparent_58%)]"
      />
      <div className="relative z-10 min-h-screen">{children}</div>
    </motion.div>
  )
}
