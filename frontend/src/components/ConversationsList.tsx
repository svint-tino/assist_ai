import { MessageSquare, Plus } from "lucide-react"

type Chat = {
  id: string
  title: string
}

export function ConversationsList({
  chatHistory,
  handleNewChat,
  handleConversationClick,
  setShowChatHistory,
  setActiveSection,
}: {
  chatHistory: Chat[]
  handleNewChat: () => void
  handleConversationClick: (chat: Chat) => void
  setShowChatHistory: (show: boolean) => void
  setActiveSection: (section: string) => void
}) {
  return (
    <div className="space-y-4 p-3">
      <button
        onClick={handleNewChat}
        className="flex items-center w-full text-black hover:bg-gray-100 rounded text-sm px-3 py-2 rounded border border-gray-200"
      >
        <MessageSquare className="mr-2 h-4 w-4" />
        Nouvelle conversation
      </button>

      <div className="space-y-2">
        <p className="flex items-center w-full px-3 text-sm font-semibold mb-2">Conversations récentes</p>

        {chatHistory.slice(0, 5).map((chat) => (
          <button
            key={chat.id}
            onClick={() => handleConversationClick(chat)}
            className="flex items-center w-full px-3 py-2 rounded hover:bg-gray-100 text-sm"
          >
            <MessageSquare className="mr-2 h-3 w-3" />
            <span className="truncate">{chat.title}</span>
          </button>
        ))}

        <button
          onClick={() => {
            setShowChatHistory(true)
            setActiveSection("chat-history")
          }}
          className="flex items-center w-full px-3 py-2 text-sm text-gray-500 hover:bg-gray-50 rounded"
        >
          <Plus className="mr-2 h-3 w-3" />
          Voir tout l'historique
        </button>
      </div>
    </div>
  )
}