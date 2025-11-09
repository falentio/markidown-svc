import { readFileSync } from "node:fs"

const file = readFileSync("./test-data/SCRUMstudy-SBOK-Guide-2016.pdf")

const promises = [] as Promise<void>[]
let success = 0
for (let i = 0; i < 1; i++) {
  console.log("starting " + i)
  const signal = AbortSignal.timeout(120000)
  const start = Date.now()
  const body = new FormData()
  body.set("file", new File([file], "SCRUMstudy-SBOK-Guide-2016.pdf"))
  const p = fetch("https://markidown-svc.fly.dev/transform", {
    method: "POST",
    headers: {
    },
    body,
    signal,
  }).then(async r => {
    const end = Date.now()
    const delta = end - start
    console.log(`process ${i} processed in ${(delta/60_000|0).toLocaleString()}m ${((delta % 60_000) / 1000) |0}s`)
    console.log(`status: ${r.status}`)
    if (r.status !== 200) {
      console.log(`error: ${await r.text()}`)
    } else {
    success++
    }
  }).catch(e => {
    console.error(e)
  })
}
await Promise.all(promises)
console.log(`success: ${success}`)
