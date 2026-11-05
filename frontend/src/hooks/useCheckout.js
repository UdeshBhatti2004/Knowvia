import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { createSubscription } from '../services/api'
import { USAGE_KEY, useUsage } from './useUsage'

const CHECKOUT_SRC = 'https://checkout.razorpay.com/v1/checkout.js'
const POLL_MS = 3000
const MAX_POLLS = 20

function loadCheckoutScript() {
  if (window.Razorpay) return Promise.resolve()
  return new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = CHECKOUT_SRC
    script.onload = resolve
    script.onerror = () =>
      reject(new Error('Could not load the payment window. Check your connection.'))
    document.body.appendChild(script)
  })
}

// Opens Razorpay checkout. The popup closing does NOT change the plan:
// the webhook does. So after payment we poll /usage until the plan flips.
export function useCheckout() {
  const queryClient = useQueryClient()
  const { data: usage } = useUsage()

  // idle | starting | activating | timeout
  const [phase, setPhase] = useState('idle')
  const [targetPlan, setTargetPlan] = useState(null)
  const [error, setError] = useState('')

  const activated = phase === 'activating' && usage?.plan === targetPlan
  const status = activated ? 'done' : phase

  useEffect(() => {
    if (status !== 'activating') return undefined

    let polls = 0
    const id = setInterval(() => {
      polls += 1
      if (polls > MAX_POLLS) {
        clearInterval(id)
        setPhase('timeout')
        return
      }
      queryClient.invalidateQueries({ queryKey: USAGE_KEY })
    }, POLL_MS)

    return () => clearInterval(id)
  }, [status, queryClient])

  async function startCheckout(plan, label) {
    setError('')
    setPhase('starting')
    try {
      const { subscription_id, key_id } = await createSubscription(plan)
      await loadCheckoutScript()

      const checkout = new window.Razorpay({
        key: key_id,
        subscription_id,
        name: 'Knowvia',
        description: `${label} plan, monthly`,
        theme: { color: '#7c3aed' },
        handler: () => {
          setTargetPlan(plan)
          setPhase('activating')
        },
        modal: {
          ondismiss: () => setPhase((p) => (p === 'starting' ? 'idle' : p)),
        },
      })

      checkout.on('payment.failed', (response) => {
        setError(response?.error?.description || 'Payment failed. Try again.')
        setPhase('idle')
      })

      checkout.open()
    } catch (err) {
      setError(err.message)
      setPhase('idle')
    }
  }

  return {
    startCheckout,
    status,
    error,
    busy: status === 'starting' || status === 'activating',
  }
}