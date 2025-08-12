import React, { useState } from 'react'
import { encryptJSON } from '../crypto'
import { createAccount } from '../api'

export default function AccountForm({ masterKey, onCreated }) {
  const [form, setForm] = useState({
    title: '',
    username: '',
    email: '',
    password: '',
    phone: '',
    note: '',
    tags: '',
    totp: ''
  })
  const [busy, setBusy] = useState(false)

  const set = (k) => (e) => setForm(s => ({...s, [k]: e.target.value}))

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      const plain = { ...form }
      const { ciphertext, nonce, salt } = await encryptJSON(plain, masterKey)
      const saved = await createAccount({
        ciphertext, nonce, salt, title: form.title || '', tags: form.tags || ''
      })
      onCreated?.(saved)
      setForm({ title:'', username:'', email:'', password:'', phone:'', note:'', tags:'', totp:'' })
    } catch (err) {
      alert('Lỗi tạo bản ghi: ' + err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="card">
      <h3>Thêm tài khoản</h3>
      <div className="row">
        <div><label>Tiêu đề</label><input value={form.title} onChange={set('title')} /></div>
        <div><label>Tags</label><input value={form.tags} onChange={set('tags')} placeholder="work,personal,..." /></div>
      </div>
      <div className="row">
        <div><label>Username</label><input value={form.username} onChange={set('username')} /></div>
        <div><label>Email</label><input value={form.email} onChange={set('email')} /></div>
      </div>
      <div className="row">
        <div><label>Password</label><input value={form.password} onChange={set('password')} type="password" /></div>
        <div><label>Phone</label><input value={form.phone} onChange={set('phone')} /></div>
      </div>
      <div className="row">
        <div><label>2FA / TOTP</label><input value={form.totp} onChange={set('totp')} /></div>
        <div><label>Ghi chú</label><input value={form.note} onChange={set('note')} /></div>
      </div>
      <div style={{ marginTop: 12 }}>
        <button disabled={busy}>{busy ? 'Đang lưu...' : 'Lưu (mã hoá client-side)'}</button>
      </div>
    </form>
  )
}

