import React from 'react'
import MasterKeyGate from './components/MasterKeyGate'
import { MasterKeyProvider, useMasterKey } from './MasterKeyContext'
import AccountForm from './components/AccountForm'
import AccountList from './components/AccountList'

function AppInner() {
  const { masterKey } = useMasterKey()
  return (
    <MasterKeyGate>
      <div className="container">
        <div className="card" style={{marginBottom:16}}>
          <h2>Account Vault (E2EE AES-256-GCM)</h2>
          <p>Frontend mã hoá trước khi gửi lên server. DB & Sheets chỉ chứa ciphertext.</p>
        </div>
        <AccountForm masterKey={masterKey} onCreated={()=>{}} />
        <AccountList masterKey={masterKey} />
      </div>
    </MasterKeyGate>
  )
}

export default function App() {
  return (
    <MasterKeyProvider>
      <AppInner />
    </MasterKeyProvider>
  )
}

