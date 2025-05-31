import { createClient } from '@supabase/supabase-js'

// Tu peux récupérer ces infos depuis app.supabase.com > Project Settings > API
const supabaseUrl = 'https://zjjikrertpqjmxjhdrjo.supabase.co'
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpqamlrcmVydHBxam14amhkcmpvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDg2NDgwNjEsImV4cCI6MjA2NDIyNDA2MX0.8XGRJMP2IjXqB4Q7Uw2tLqFNTnenUVerJyLyp21DhLg'

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
