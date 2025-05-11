type BackButtonProps = {
    onClick: () => void
  }
  
  export function BackButton({ onClick }: BackButtonProps) {
    return (
      <button
        onClick={onClick}
        className="absolute top-4 left-4 flex items-center text-gray-700 hover:text-black"
      >
        <svg
          className="h-5 w-5 mr-2"
          fill="none"
          stroke="currentColor"
          strokeWidth={2}
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        <span>Back</span>
      </button>
    )
  }
  