import { useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { CookingLoader } from './CookingLoader'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

export function InputBox({ 
  shopName,
  onFirstMessage,
}: {
  shopName: string
  onFirstMessage: () => void
}) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
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

    const userMessage = { role: 'user', content: question } as const
    setMessages(prev => [userMessage, ...prev])
    onFirstMessage()
    setQuestion('')
    setIsLoading(true)

    try {
      const res = await fetch('http://localhost:4000/api/assistant/conversation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: question,
          shop: shopName,
        }),
      })

      const data = await res.json()
      const assistantMessage = { role: 'assistant', content: data.assistant_reply } as const
      setMessages(prev => [assistantMessage, ...prev])
    } catch (err) {
      console.error('Error fetching response:', err)
      setMessages(prev => [
        { role: 'assistant', content: 'Erreur de réponse de KOOC.' },
        ...prev,
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      <div className="flex flex-col-reverse gap-4 max-h-[75vh] overflow-y-auto w-[600px]">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`max-w-[80%] px-4 py-2 rounded-lg text-sm ${
              msg.role === 'user'
                ? 'bg-gray-100 self-end text-right'
                : 'bg-[#faf9f9] self-start text-left'
            }`}
          >
            {msg.role === 'assistant' ? (
              <div className="prose prose-sm max-w-none text-gray-800">
                <ReactMarkdown>
                  {msg.content}
                </ReactMarkdown>
              </div>
            ) : (
              msg.content
            )}
          </div>
        ))}
      </div>

      {isLoading && (
        <div className="flex items-center justify-center gap-2 text-gray-600">
          <CookingLoader />
          <span className="italic text-sm">KOOC mijote...</span>
        </div>
      )}

      <div className="flex gap-2 items-start justify-between w-[600px]">
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
          className="bg-black text-white px-6 py-2 rounded hover:bg-gray-800 disabled:opacity-50"
          disabled={isLoading}
        >
          Send
        </button>
      </div>
    </div>
  )
}