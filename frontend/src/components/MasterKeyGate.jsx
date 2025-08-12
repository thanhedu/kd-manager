import React, { useState } from 'react'
import { useMasterKey } from '../MasterKeyContext'

export default function MasterKeyGate({ children }) {
  const { masterKey, unlock, lock } = useMasterKey()
  const [input, setInput] = useState('')

  if (!masterKey) {
    return (
      <div className="container">
        <div className="card">
          <h2>Nhập Master Key</h2>
          <p>Khoá này chỉ lưu trong RAM và dùng để mã hoá/giải mã cục bộ.</p>
          <input type="password" placeholder="Master Key"
                 value={input} onChange={e=>setInput(e.target.value)} />
          <div style={{ marginTop: 12 }}>
            <button onClick={()=> unlock(input || '')}>Bắt đầu</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="container" style={{display:'flex', justifyContent:'space-between', alignItems:'center'}}>
        <h3>🔐 Đã khoá bằng Master Key (chỉ trong phiên)</h3>
        <button className="ghost" onClick={lock}>Khoá lại</button>
      </div>
      {children}
    </div>
  )
}

