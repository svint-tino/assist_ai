import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

// Utility function to concatenate class names
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}