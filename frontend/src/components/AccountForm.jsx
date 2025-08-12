import React, { useState } from 'react'
import { encryptJSON } from '../crypto'
import { createAccount } from '../api'

export default function AccountForm({ masterKey, onCreated }) {
  // ====== form gốc (dùng cho mã hoá & hiển thị) ======
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
  const set = (k) => (e) => setForm(s => ({ ...s, [k]: e.target.value }))

  // ====== Quick meta fields (nhập nhanh, sẽ gửi vào payload.meta) ======
  const [platform, setPlatform] = useState("")
  const [url, setUrl] = useState("")
  const [note, setNote] = useState("")
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [emailRecovery, setEmailRecovery] = useState("")
  const [dob, setDob] = useState("")         // yyyy-mm-dd
  const [phone, setPhoneMeta] = useState("") // meta riêng, khác form.phone nếu bạn muốn
  const [twofa, setTwofa] = useState("")     // "true" | "false" | ""
  const [industry, setIndustry] = useState("")
  const [expiresAt, setExpiresAt] = useState("")  // yyyy-mm-dd
  const [priority, setPriority] = useState("")    // Cao / Trung_binh / Thap
  const [status, setStatus] = useState("")        // Dang_dung / Tam_khoa / Het_han

  const PRIORITIES = ["Cao", "Trung_binh", "Thap"]
  const STATUSES   = ["Dang_dung", "Tam_khoa", "Het_han"]
  const INDUSTRIES = ["Facebook", "YouTube", "Zalo", "Shopee", "Khac"]

  async function submit(e) {
    e.preventDefault()
    setBusy(true)
    try {
      // phần plain để mã hoá vẫn giữ nguyên
      const plain = { ...form }
      const { ciphertext, nonce, salt } = await encryptJSON(plain, masterKey)

      // gom meta để backend ghi ra Google Sheet theo GOOGLE_SHEETS_COLUMNS
      const meta = {
        platform,
        url,
        note,
        username,
        email,
        email_recovery: emailRecovery,
        dob,
        phone: phoneMetaValue(),  // ưu tiên meta.phone nếu có, không thì lấy form.phone
        twofa,
        industry,
        expires_at: expiresAt,
        priority,
        status
      }

      const saved = await createAccount({
        ciphertext,
        nonce,
        salt,
        title: form.title || '',
        tags: form.tags || '',
        meta
      })

      onCreated?.(saved)

      // reset nhanh để nhập tiếp
      setForm({ title: '', username: '', email: '', password: '', phone: '', note: '', tags: '', totp: '' })
      setPlatform(''); setUrl(''); setNote(''); setUsername(''); setEmail(''); setEmailRecovery('')
      setDob(''); setPhoneMeta(''); setTwofa(''); setIndustry(''); setExpiresAt(''); setPriority(''); setStatus('')
    } catch (err) {
      alert('Lỗi tạo bản ghi: ' + err.message)
    } finally {
      setBusy(false)
    }
  }

  const phoneMetaValue = () => (phone || form.phone || '')

  return (
    <form onSubmit={submit} className="card">
      <h3>Thêm tài khoản</h3>

      {/* Khối gốc (nếu bạn đang dùng) */}
      <div className="row">
        <div>
          <label>Tiêu đề</label>
          <input value={form.title} onChange={set('title')} />
        </div>
        <div>
          <label>Tags</label>
          <input value={form.tags} onChange={set('tags')} placeholder="work,personal,..." />
        </div>
      </div>
      <div className="row">
        <div>
          <label>Username</label>
          <input value={form.username} onChange={set('username')} />
        </div>
        <div>
          <label>Email</label>
          <input type="email" value={form.email} onChange={set('email')} />
        </div>
      </div>
      <div className="row">
        <div>
          <label>Password</label>
          <input value={form.password} onChange={set('password')} type="password" />
        </div>
        <div>
          <label>Phone</label>
          <input value={form.phone} onChange={set('phone')} />
        </div>
      </div>
      <div className="row">
        <div>
          <label>2FA / TOTP</label>
          <input value={form.totp} onChange={set('totp')} />
        </div>
        <div>
          <label>Ghi chú</label>
          <input value={form.note} onChange={set('note')} />
        </div>
      </div>

      {/* ====== Nhập nhanh (meta) – gọn 1 màn hình, tối ưu mobile ====== */}
      <div className="meta-form" style={{ marginTop: 12 }}>
        <div className="full">
          <label>Nền tảng</label>
          <input placeholder="Facebook / Zalo / ..." value={platform} onChange={e => setPlatform(e.target.value)} />
        </div>

        <div>
          <label>Link web</label>
          <input type="url" placeholder="https://..." value={url} onChange={e => setUrl(e.target.value)} />
        </div>

        <div>
          <label>Username</label>
          <input placeholder="username" value={username} onChange={e => setUsername(e.target.value)} />
        </div>

        <div>
          <label>Email</label>
          <input type="email" placeholder="email@domain.com" value={email} onChange={e => setEmail(e.target.value)} />
        </div>

        <div>
          <label>Email recovery</label>
          <input type="email" placeholder="email recovery" value={emailRecovery} onChange={e => setEmailRecovery(e.target.value)} />
        </div>

        <div>
          <label>Số điện thoại (meta)</label>
          <input inputMode="tel" placeholder="090..." value={phone} onChange={e => setPhoneMeta(e.target.value)} />
        </div>

        <div>
          <label>Ngày sinh</label>
          <input type="date" value={dob} onChange={e => setDob(e.target.value)} />
        </div>

        <div>
          <label>Hạn sử dụng</label>
          <input type="date" value={expiresAt} onChange={e => setExpiresAt(e.target.value)} />
        </div>

        <div>
          <label>Mức ưu tiên</label>
          <select value={priority} onChange={e => setPriority(e.target.value)}>
            <option value="">--</option>
            {PRIORITIES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </div>

        <div>
          <label>Trạng thái</label>
          <select value={status} onChange={e => setStatus(e.target.value)}>
            <option value="">--</option>
            {STATUSES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </div>

        <div>
          <label>Lĩnh vực</label>
          <select value={industry} onChange={e => setIndustry(e.target.value)}>
            <option value="">--</option>
            {INDUSTRIES.map(x => <option key={x} value={x}>{x}</option>)}
          </select>
        </div>

        <div>
          <label>2FA</label>
          <select value={twofa} onChange={e => setTwofa(e.target.value)}>
            <option value="">--</option>
            <option value="true">Có</option>
            <option value="false">Không</option>
          </select>
        </div>

        <div className="full">
          <label>Ghi chú chung</label>
          <textarea placeholder="Ghi chú..." value={note} onChange={e => setNote(e.target.value)} />
        </div>
      </div>
      {/* ====== Hết cụm meta ====== */}

      <div style={{ marginTop: 12 }}>
        <button disabled={busy}>{busy ? 'Đang lưu...' : 'Lưu (mã hoá client-side)'}</button>
      </div>
    </form>
  )
}
