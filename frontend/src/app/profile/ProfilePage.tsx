import { useState } from 'react'
import { User, Mail, X, Camera, Shield, Clock } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

interface UserProfile {
  name: string
  email: string
  avatar: string
  role: string
  lastLogin: string
  apiKey?: string
}

export function ProfilePage({
  user,
  onClose,
}: {
  user: UserProfile
  onClose: () => void
}) {
  const navigate = useNavigate()
  const [editedUser, setEditedUser] = useState<UserProfile>(user)
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)

  const handleClose = () => {
    onClose()
    navigate('/')
  }

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = (e) => {
        const result = e.target?.result as string
        setAvatarPreview(result)
        setEditedUser(prev => ({ ...prev, avatar: result }))
      }
      reader.readAsDataURL(file)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h1 className="text-2xl font-bold">Mon Profil</h1>
          <button
            onClick={handleClose}
            className="p-2 hover:bg-gray-100 rounded-lg"
            title="Fermer le profil"
            aria-label="Fermer le profil"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Avatar et nom */}
          <div className="flex items-center gap-6">
            <div className="relative">
              <div className="w-24 h-24 rounded-full overflow-hidden bg-gray-100">
                {(avatarPreview || editedUser.avatar) ? (
                  <img
                    src={avatarPreview || editedUser.avatar}
                    alt={editedUser.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <User className="w-full h-full p-4 text-gray-400" />
                )}
              </div>
              <label className="absolute bottom-0 right-0 bg-black text-white p-2 rounded-full cursor-pointer">
                <Camera className="w-4 h-4" />
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleAvatarChange}
                  className="hidden"
                />
              </label>
            </div>

            <div className="flex-1">
              <p className="text-xl font-semibold">{user.name}</p>
              <div className="flex items-center gap-2 text-gray-600">
                <Mail className="w-4 h-4" />
                <span>{user.email}</span>
              </div>
            </div>
          </div>

          {/* Informations système */}
          <div className="bg-gray-50 p-4 rounded-lg space-y-4">
            <div className="flex items-center gap-3">
              <Shield className="w-5 h-5 text-blue-600" />
              <div>
                <p className="font-medium">Rôle</p>
                <p className="text-sm text-gray-600">{user.role}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 text-purple-600" />
              <div>
                <p className="font-medium">Dernière connexion</p>
                <p className="text-sm text-gray-600">
                  {new Date(user.lastLogin).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}