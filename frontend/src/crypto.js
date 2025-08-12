// E2EE AES-256-GCM với PBKDF2(SHA-256)
// Không lưu master key vào storage; chỉ giữ trong state.

const textEncoder = new TextEncoder()
const textDecoder = new TextDecoder()

function toB64(buf) {
  return btoa(String.fromCharCode(...new Uint8Array(buf)))
}
function fromB64(b64) {
  return Uint8Array.from(atob(b64), c => c.charCodeAt(0))
}

async function deriveKey(masterKeyStr, saltBytes, iterations = 310000) {
  const mkRaw = textEncoder.encode(masterKeyStr)
  const baseKey = await crypto.subtle.importKey(
    'raw', mkRaw, { name: 'PBKDF2' }, false, ['deriveKey']
  )
  return await crypto.subtle.deriveKey(
    { name: 'PBKDF2', salt: saltBytes, iterations, hash: 'SHA-256' },
    baseKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  )
}

export async function encryptJSON(obj, masterKeyStr) {
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const key = await deriveKey(masterKeyStr, salt)
  const plaintext = textEncoder.encode(JSON.stringify(obj))
  const ciphertext = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    plaintext
  )
  return {
    ciphertext: toB64(ciphertext), // tag gắn sau ciphertext theo WebCrypto
    nonce: toB64(iv),
    salt: toB64(salt),
  }
}

export async function decryptJSON({ ciphertext, nonce, salt }, masterKeyStr) {
  const saltBytes = fromB64(salt)
  const iv = fromB64(nonce)
  const ct = fromB64(ciphertext)
  const key = await deriveKey(masterKeyStr, saltBytes)
  const pt = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    key,
    ct
  )
  return JSON.parse(textDecoder.decode(pt))
}

