import { useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import { CookingLoader } from './CookingLoader'
import { VisualChart } from './VisualChart'

type Message = {
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'visual' | 'composite'
  visuals?: string[] // Pour les messages composites
  isStreamingComplete?: boolean // Pour savoir si on peut afficher les visuels
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
  const [, setIsStreaming] = useState(false)
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

    const userMessage: Message = { role: 'user', content: question, type: 'text' }
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

      const reader = res.body?.getReader()
      const decoder = new TextDecoder('utf-8')

      // Créer un message composite dès le début
      const assistantMessage: Message = { 
        role: 'assistant', 
        content: '', 
        type: 'composite',
        visuals: [],
        isStreamingComplete: false
      }
      setMessages(prev => [assistantMessage, ...prev])
      setIsStreaming(true)

      if (reader) {
        while (true) {
          const { value, done } = await reader.read()
          if (done) {
            // Marquer le streaming comme terminé
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[0]
              if (last?.role === 'assistant' && last.type === 'composite') {
                updated[0] = { ...last, isStreamingComplete: true }
              }
              return updated
            })
            setIsStreaming(false)
            break
          }
          const chunk = decoder.decode(value)

          if (chunk.startsWith('[VISUAL]')) {
            const url = chunk.replace('[VISUAL]', '').trim()
            const fullUrl = url.startsWith('http') ? url : `http://localhost:4000${url}`
            
            // Ajouter le visuel au message composite (mais ne pas l'afficher encore)
            setMessages(prev => {
              const updated = [...prev]
              const last = updated[0]
              if (last?.role === 'assistant' && last.type === 'composite') {
                updated[0] = { 
                  ...last, 
                  visuals: [...(last.visuals || []), fullUrl] 
                }
              }
              return updated
            })
            continue
          }

          // Mise à jour du contenu textuel
          setMessages(prev => {
            const updated = [...prev]
            const last = updated[0]
            if (last?.role === 'assistant' && last.type === 'composite') {
              updated[0] = { ...last, content: last.content + chunk }
            }
            return updated
          })
        }
      }
    } catch (err) {
      console.error('Streaming error:', err)
      const errorMessage: Message = { role: 'assistant', content: 'Erreur de réponse de KOOC.', type: 'text' }
      setMessages(prev => [errorMessage, ...prev])
      setIsStreaming(false)
    } finally {
      setIsLoading(false)
    }
  }

  const renderMessage = (msg: Message, index: number) => {
    const baseClasses = `max-w-[80%] px-4 py-2 rounded-lg text-sm ${
      msg.role === 'user'
        ? 'bg-gray-100 self-end text-right'
        : 'bg-[#faf9f9] self-start text-left'
    }`

    if (msg.type === 'composite') {
      return (
        <div key={index} className={baseClasses}>
          {/* Contenu textuel */}
          {msg.content && (
            <div className="prose prose-sm max-w-none text-gray-800">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          )}
          
          {/* Graphiques à la suite - seulement si le streaming est terminé */}
          {msg.visuals && msg.visuals.length > 0 && msg.isStreamingComplete && (
            <div className="mt-4 space-y-4">
              {msg.visuals.map((url, idx) => (
                <VisualChart key={idx} url={url} />
              ))}
            </div>
          )}
        </div>
      )
    }

    if (msg.type === 'visual') {
      return (
        <div key={index} className={baseClasses}>
          <VisualChart url={msg.content} />
        </div>
      )
    }

    // Message texte simple
    return (
      <div key={index} className={baseClasses}>
        {msg.role === 'assistant' ? (
          <div className="prose prose-sm max-w-none text-gray-800">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        ) : (
          msg.content
        )}
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-4 w-full">
      <div className="flex flex-col-reverse gap-4 max-h-[75vh] overflow-y-auto w-[600px]">
        {messages.map((msg, index) => renderMessage(msg, index))}
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