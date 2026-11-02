import { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'

function PasswordInput({ className = '', wrapperClassName = '', ...props }) {
  const [visible, setVisible] = useState(false)

  return (
    <div className={`relative ${wrapperClassName}`}>
      <input
        {...props}
        type={visible ? 'text' : 'password'}
        className={`${className} pr-10`}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-label={visible ? 'Hide password' : 'Show password'}
        className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-zinc-500 transition-colors hover:text-zinc-300"
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  )
}

export default PasswordInput