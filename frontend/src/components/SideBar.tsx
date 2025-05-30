import { X } from "lucide-react"
import { NavUser } from "./NavUser"
import { ConversationsList } from "./ConversationsList"

type Chat = {
  id: string
  title: string
}

export function Sidebar({
  user,
  chatHistory,
  handleNewChat,
  handleConversationClick,
  setShowChatHistory,
  setActiveSection,
  onLogout,
  onClose,
}: {
  user: {
    name: string
    email: string
    avatar: string
  }
  chatHistory: Chat[]
  handleNewChat: () => void
  handleConversationClick: (chat: Chat) => void
  setShowChatHistory: (show: boolean) => void
  setActiveSection: (section: string) => void
  onLogout: () => void
  onClose?: () => void
}) {

  return (
    <aside className="w-[260px] h-screen border-r border-gray-200 bg-white flex flex-col justify-between p-4 relative">
      {/* Bouton de fermeture mobile */}
      {onClose && (
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 md:hidden z-10"
          aria-label="Fermer le menu"
        >
          <X className="w-5 h-5" />
        </button>
      )}

      <div className="flex-1 overflow-y-auto">

        <ConversationsList
          chatHistory={chatHistory}
          handleNewChat={handleNewChat}
          handleConversationClick={handleConversationClick}
          setShowChatHistory={setShowChatHistory}
          setActiveSection={setActiveSection}
        />
      </div>
        <NavUser
          user={user}
          onLogout={onLogout}
        />
    </aside>
  )
}