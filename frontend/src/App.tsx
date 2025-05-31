import { useState } from "react"
import { Menu } from "lucide-react"
import { Routes, Route } from "react-router-dom"

import logo from "./assets/logooblanc.png"
import logoSymbole from "./assets/logooblancsymbole.png"
import { InputBox } from "./app/chat/InputBox"
import { ProfilePage } from "./app/profile/ProfilePage"
import { Sidebar } from "./components/SideBar"
import { useAuth } from "./AuthContext"
import AuthForm from "./AuthForm"

type Chat = {
  id: string
  title: string
}

export default function App() {
  const { user, loading, signOut } = useAuth()
  
  const [shopName, setShopName] = useState("")
  const [confirmedShop, setConfirmedShop] = useState("")
  const [hasSentMessage, setHasSentMessage] = useState(false)

  const [chatHistory, setChatHistory] = useState<Chat[]>([])
  const [, setSelectedChat] = useState<Chat | null>(null)
  const [, setShowChatHistory] = useState(false)
  const [, setActiveSection] = useState("chat")

  const [isSidebarOpen, setIsSidebarOpen] = useState(true)
  const toggleSidebar = () => setIsSidebarOpen((prev) => !prev)

  const handleNewChat = () => {
    const newChat = {
      id: Date.now().toString(),
      title: `Nouvelle conversation ${chatHistory.length + 1}`,
    }
    setChatHistory([newChat, ...chatHistory])
    setSelectedChat(newChat)
    setActiveSection("chat")
  }

  const handleConversationClick = (chat: Chat) => {
    setSelectedChat(chat)
    setActiveSection("chat")
    if (window.innerWidth < 768) {
      setIsSidebarOpen(false)
    }
  }

  const handleLogout = async () => {
    try {
      await signOut()
      // Reset de l'état de l'app
      setConfirmedShop("")
      setHasSentMessage(false)
      setSelectedChat(null)
      setChatHistory([])
      setIsSidebarOpen(false)
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error)
    }
  }

  // Affichage du loader pendant la vérification de l'auth
  if (loading) {
    return (
      <div className="min-h-screen bg-[#faf9f9] flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-black mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    )
  }

  // Si pas connecté, afficher le formulaire d'auth
  if (!user) {
    return <AuthForm />
  }

  // Si connecté mais pas de shop configuré
  if (!confirmedShop) {
    return (
      <div className="min-h-screen bg-[#faf9f9] flex items-center justify-center p-4">
        <div className="w-full max-w-[300px] flex flex-col gap-4">
          <div className="text-center mb-4">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Bienvenue {user.user_metadata?.full_name} !
            </h2>
            <p className="text-gray-600 text-sm">
              Configurez votre boutique pour commencer
            </p>
          </div>
          
          <input
            type="url"
            value={shopName}
            onChange={(e) => setShopName(e.target.value)}
            placeholder="Lien de votre boutique (exemple.com)"
            className="border border-gray-300 rounded px-4 py-2 text-base w-full"
          />
          <button
            onClick={() => {
              if (shopName.trim()) setConfirmedShop(shopName.trim())
            }}
            className="bg-black text-white px-6 py-2 rounded hover:bg-gray-800 w-full"
          >
            Accéder à KOOC
          </button>
        </div>
      </div>
    )
  }

  // Interface principale de l'app
  return (
    <div className="min-h-screen flex bg-[#faf9f9] relative">
      {isSidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {isSidebarOpen && (
        <div
          className={`fixed md:relative z-50 md:z-auto transform transition-transform duration-300 ease-in-out translate-x-0`}
        >
          <Sidebar
            user={{
              name: user.user_metadata?.full_name || "Utilisateur",
              email: user.email || "",
              avatar: user.user_metadata?.avatar_url || `https://i.pravatar.cc/150?u=${user.email}`,
            }}
            chatHistory={chatHistory}
            handleNewChat={handleNewChat}
            handleConversationClick={handleConversationClick}
            setShowChatHistory={setShowChatHistory}
            setActiveSection={setActiveSection}
            onLogout={handleLogout}
            onClose={() => setIsSidebarOpen(false)}
          />
        </div>
      )}

      <div className="flex-1 grid grid-rows-[auto_1fr_auto] min-h-screen">
        <div className="flex items-center justify-between p-4">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleSidebar}
              className="text-gray-600 hover:text-black focus:outline-none p-1"
              title="Toggle Sidebar"
            >
              <Menu className="w-6 h-6" />
            </button>
          </div>

          {hasSentMessage && (
            <div className="flex-grow flex justify-center">
              <img
                src={logoSymbole}
                alt="KOOC small"
                className="w-8 h-8 sm:w-10 sm:h-10 object-contain"
              />
            </div>
          )}
        </div>

        {/* Main zone avec routes */}
        <Routes>
          <Route
            path="/profile"
            element={
              <ProfilePage
                user={{
                  name: user.user_metadata?.full_name || "Utilisateur",
                  email: user.email || "",
                  avatar: user.user_metadata?.avatar_url || `https://i.pravatar.cc/150?u=${user.email}`,
                  role: "utilisateur",
                  lastLogin: new Date().toISOString(),
                }}
                onClose={() => setActiveSection("chat")}
              />
            }
          />
          <Route
            path="*"
            element={
              <>
                {/* Logo KOOC visible au début */}
                <div className="flex items-center justify-center px-4">
                  {!hasSentMessage && (
                    <img
                      src={logo}
                      alt="KOOC Logo"
                      className="w-[150px] h-[120px] sm:w-[200px] sm:h-[150px] object-contain"
                    />
                  )}
                </div>

                <div className="pb-4 sm:pb-12 px-4">
                  <InputBox
                    shopName={confirmedShop}
                    onFirstMessage={() => setHasSentMessage(true)}
                  />
                </div>
              </>
            }
          />
        </Routes>
      </div>
    </div>
  )
}