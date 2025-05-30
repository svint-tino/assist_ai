import { useState, useRef, useEffect } from "react";
import { ChevronDown, User, Settings, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";

export function NavUser({
  user,
  onLogout,
}: {
  user: {
    name: string;
    email: string;
    avatar: string;
  };
  onLogout?: () => void;
}) {
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);
  const [imageError, setImageError] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  // Fermer le menu en cliquant à l’extérieur
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsAccountMenuOpen(false);
      }
    }

    if (isAccountMenuOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isAccountMenuOpen]);

  const handleMenuAction = (action?: () => void) => {
    if (action) action();
    setIsAccountMenuOpen(false);
  };

  const handleToggle = () => {
    setIsAccountMenuOpen(!isAccountMenuOpen);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      handleToggle();
    }
    if (e.key === "Escape") {
      setIsAccountMenuOpen(false);
    }
  };

  const menuItems = [
    {
      icon: User,
      label: "Profil",
      action: () => navigate("/profile"),
      danger: false,
    },
    {
      icon: Settings,
      label: "Paramètres",
      action: () => navigate("/settings"), // tu peux l'activer plus tard
      danger: false,
    },
    {
      icon: LogOut,
      label: "Déconnexion",
      action: onLogout,
      danger: true,
    },
  ];

  return (
    <div className="mt-auto border-t" ref={menuRef}>
      <div
        className="p-3 cursor-pointer"
        onClick={handleToggle}
        role="button"
        tabIndex={0}
        aria-expanded={isAccountMenuOpen ? "true" : "false"}
        aria-haspopup="menu"
        aria-label="Menu utilisateur"
        onKeyDown={handleKeyDown}
      >
        <div className="bg-gray-50 p-3 rounded-lg transition-colors duration-200 hover:bg-gray-100">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <img
                  src={imageError ? "/api/placeholder/32/32" : user.avatar}
                  alt={user.name}
                  className="h-8 w-8 rounded-full object-cover"
                  onError={() => setImageError(true)}
                />
                {imageError && (
                  <div className="absolute inset-0 bg-gray-300 rounded-full flex items-center justify-center">
                    <User className="w-4 h-4 text-gray-600" />
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-medium text-sm truncate">{user.name}</p>
                <p className="text-xs text-gray-500 truncate">{user.email}</p>
              </div>
            </div>
            <ChevronDown
              className={`w-4 h-4 transition-transform duration-200 text-gray-400 ${
                isAccountMenuOpen ? "rotate-180" : ""
              }`}
            />
          </div>
        </div>
      </div>

      <div
        className={`space-y-1 mt-2 overflow-hidden transition-all duration-200 ${
          isAccountMenuOpen ? "max-h-48 opacity-100" : "max-h-0 opacity-0"
        }`}
        role="menu"
        aria-hidden={isAccountMenuOpen ? "true" : "false"}
      >
        {menuItems.map((item, index) => {
          const Icon = item.icon;
          return (
            <div key={index} className="w-full">
              <button
                onClick={() => handleMenuAction(item.action)}
                role="menuitem"
                tabIndex={isAccountMenuOpen ? 0 : -1}
                className={`w-full flex items-center px-3 py-2 text-sm text-left rounded transition-colors duration-150 ${
                  item.danger
                    ? "text-red-600 hover:text-red-700 hover:bg-red-50 focus:bg-red-50"
                    : "text-gray-700 hover:bg-gray-100 focus:bg-gray-100"
                } focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-inset`}
              >
                <Icon className="mr-2 h-4 w-4" />
                {item.label}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}