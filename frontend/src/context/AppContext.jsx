// Authentication and language state for the whole application.
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { api, clearToken, getToken, saveToken } from '../api/client'
import { t as translate } from '../i18n/translations'

const AppContext = createContext(null)

const FARMER_KEY = 'mlimismart_farmer'
const LANGUAGE_KEY = 'mlimismart_language'

export function AppProvider({ children }) {
  const [farmer, setFarmer] = useState(() => {
    const stored = localStorage.getItem(FARMER_KEY)
    return stored ? JSON.parse(stored) : null
  })
  const [language, setLanguage] = useState(
    () => localStorage.getItem(LANGUAGE_KEY) || 'NY',
  )
  const [booting, setBooting] = useState(Boolean(getToken()))

  // Confirm a stored token is still valid before trusting the cached profile.
  useEffect(() => {
    if (!getToken()) {
      setBooting(false)
      return
    }
    let cancelled = false
    api
      .get('/auth/me')
      .then(({ data }) => {
        if (cancelled) return
        setFarmer(data)
        localStorage.setItem(FARMER_KEY, JSON.stringify(data))
        setLanguage(data.language)
      })
      .catch(() => {
        if (!cancelled) setFarmer(null)
      })
      .finally(() => {
        if (!cancelled) setBooting(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const applySession = useCallback((data) => {
    saveToken(data.access_token)
    localStorage.setItem(FARMER_KEY, JSON.stringify(data.farmer))
    setFarmer(data.farmer)
    setLanguage(data.farmer.language)
  }, [])

  const login = useCallback(
    async (phone, password) => {
      const { data } = await api.post('/auth/login', { phone, password })
      applySession(data)
      return data.farmer
    },
    [applySession],
  )

  const register = useCallback(
    async (payload) => {
      const { data } = await api.post('/auth/register', payload)
      applySession(data)
      return data.farmer
    },
    [applySession],
  )

  const logout = useCallback(() => {
    clearToken()
    setFarmer(null)
  }, [])

  const updateFarmer = useCallback((updated) => {
    setFarmer(updated)
    localStorage.setItem(FARMER_KEY, JSON.stringify(updated))
    setLanguage(updated.language)
  }, [])

  // Switching language persists it to the profile when logged in, so the
  // choice also applies to SMS replies. A failure is ignored deliberately:
  // the interface should still switch even if the save does not reach the
  // server.
  const changeLanguage = useCallback(
    (next) => {
      setLanguage(next)
      localStorage.setItem(LANGUAGE_KEY, next)
      if (farmer) {
        api
          .patch('/auth/me', { language: next })
          .then(({ data }) => updateFarmer(data))
          .catch(() => {})
      }
    },
    [farmer, updateFarmer],
  )

  const value = useMemo(
    () => ({
      farmer,
      language,
      booting,
      isAdmin: farmer?.role === 'ADMIN',
      login,
      register,
      logout,
      updateFarmer,
      changeLanguage,
      t: (key) => translate(key, language),
    }),
    [farmer, language, booting, login, register, logout, updateFarmer, changeLanguage],
  )

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) throw new Error('useApp must be used inside AppProvider')
  return context
}
