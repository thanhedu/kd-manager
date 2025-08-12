// Copy-to-clipboard + tự xóa sau TTL giây (mặc định 25s)
const TTL = Number(import.meta.env.VITE_CLIPBOARD_TTL_SEC || 25)

export async function copyEphemeral(text) {
  await navigator.clipboard.writeText(text)
  // cố gắng xóa sau TTL (nếu browser cho phép)
  setTimeout(async () => {
    try {
      const cur = await navigator.clipboard.readText()
      if (cur === text) {
        await navigator.clipboard.writeText('') // clear
      }
    } catch (_) {}
  }, TTL * 1000)
}

