import { useState } from 'react'
import logo from './assets/logooblanc.png'
import logoSymbole from './assets/logooblancsymbole.png'
import { InputBox } from './components/InputBox'
import { BackButton } from './components/BackButton'

export default function App() {
  const [shopName, setShopName] = useState('')
  const [confirmedShop, setConfirmedShop] = useState('')
  const [hasSentMessage, setHasSentMessage] = useState(false)

  if (!confirmedShop) {
    return (
      <div className="min-h-screen bg-[#faf9f9] flex items-center justify-center">
        <div className="w-[300px] flex flex-col gap-4">
          <input
            type="url"
            value={shopName}
            onChange={(e) => setShopName(e.target.value)}
            placeholder="Inser your shop link (exemple.com)"
            className="border border-gray-300 rounded px-4 py-2 text-base"
          />
          <button
            onClick={() => {
              if (shopName.trim()) setConfirmedShop(shopName.trim())
            }}
            className="bg-black text-white px-6 py-2 rounded hover:bg-gray-800"
          >
            Go to KOOC
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen grid grid-rows-[auto_1fr_auto] bg-[#faf9f9]">
      <div className="flex items-center p-4">
        <BackButton onClick={() => setConfirmedShop('')} />
        
        {hasSentMessage && (
          <div className="flex-grow flex justify-center">
            <img
              src={logoSymbole}
              alt="KOOC small"
              className="w-10 h-10 object-contain"
            />
          </div>
        )}
      </div>
  
      <div className="flex items-center justify-center">
        {!hasSentMessage && (
          <img
            src={logo}
            alt="KOOC Logo"
            className="w-[200px] h-[150px] object-contain"
          />
        )}
      </div>
  
      <div className="pb-12">
        <InputBox shopName={confirmedShop} onFirstMessage={() => setHasSentMessage(true)} />
      </div>
    </div>
  )  
}