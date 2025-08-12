import React, { createContext, useContext, useState, useCallback } from 'react'

const MasterKeyContext = createContext(null)

export function MasterKeyProvider({ children }) {
  const [masterKey, setMasterKey] = useState(null) // chỉ giữ trong RAM

  const lock = useCallback(() => setMasterKey(null), [])
  const unlock = useCallback((key) => setMasterKey(key), [])

  return (
    <MasterKeyContext.Provider value={{ masterKey, unlock, lock }}>
      {children}
    </MasterKeyContext.Provider>
  )
}

export function useMasterKey() {
  return useContext(MasterKeyContext)
}

