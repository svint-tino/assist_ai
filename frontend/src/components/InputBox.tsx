import { useRef, useState } from 'react'
import { CookingLoader } from './CookingLoader'

export function InputBox({ shopName }: { shopName: string }) {
  const [question, setQuestion] = useState('')
  const [response, setResponse] = useState('')
  const [isLoading, setIsLoading] = useState(false) // Ajout de l'état isLoading
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleInput = () => {
    const textarea = textareaRef.current
    if (textarea) {
      textarea.style.height = 'auto'
      textarea.style.height = textarea.scrollHeight + 'px'
    }
  }

  const handleSend = async () => {
    if (!question.trim() || !shopName.trim()) return

    setIsLoading(true) // Activer le loader
    const res = await fetch('http://localhost:4000/api/assistant/conversation', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: question,
        shop: shopName,
      }),
    })

    const data = await res.json()
    setResponse(data.assistant_reply)
    setIsLoading(false) // Désactiver le loader
  }

  return (
    <div className="flex flex-col gap-4">
      {response && (
        <div className="bg-gray-100 border rounded p-4 text-gray-800 w-[600px] mx-auto">
          {response}
        </div>
      )}

      {isLoading && ( // Affichage du loader
        <div className="flex items-center justify-center gap-2 mt-2 text-gray-600">
          <CookingLoader />
          <span className="italic text-sm">KOOC simmer...</span>
        </div>
      )}

      <div className="flex gap-2 items-center justify-between w-[600px] mx-auto">
        <textarea
          ref={textareaRef}
          value={question}
          onChange={(e) => {
            setQuestion(e.target.value)
            handleInput()
          }}
          placeholder="Ask your question..."
          rows={1}
          className="w-full border border-gray-300 rounded px-4 py-2 text-base resize-none max-h-[150px] overflow-y-auto"
        />

        <button
          onClick={handleSend}
          className="bg-black text-white px-6 py-2 rounded hover:bg-gray-800"
          disabled={isLoading} // Désactiver le bouton pendant le chargement
        >
          Send
        </button>
      </div>
    </div>
  )
}