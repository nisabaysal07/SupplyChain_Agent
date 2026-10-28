import { createServer, request, type Server } from 'node:http'
import type { AddressInfo } from 'node:net'
import { createApp, defineEventHandler, getRequestIP, toNodeListener } from 'h3'
import { afterAll, beforeAll, describe, expect, it } from 'vitest'
import { istemciAdresi } from '../server/utils/istemciAdresi'

describe('istemciAdresi', () => {
  it('varsayılan: başlıklar yok sayılır, bağlantının adresi kullanılır', () => {
    expect(istemciAdresi('10.0.0.5', { 'x-forwarded-for': '1.2.3.4', 'x-real-ip': '5.6.7.8' })).toBe('10.0.0.5')
  })

  it('güvenilir başlık tanımlıysa en sağdaki (proxy\'nin eklediği) adres alınır', () => {
    expect(istemciAdresi('10.0.0.1', { 'x-forwarded-for': '6.6.6.6, 203.0.113.7' }, 'x-forwarded-for')).toBe('203.0.113.7')
    expect(istemciAdresi('10.0.0.1', { 'x-real-ip': '203.0.113.7' }, 'X-Real-IP')).toBe('203.0.113.7')
    expect(istemciAdresi('10.0.0.1', { 'x-forwarded-for': '2001:db8::1' }, 'x-forwarded-for')).toBe('2001:db8::1')
  })

  it('başlık yoksa ya da adres değilse bağlantının adresi kullanılır', () => {
    expect(istemciAdresi('10.0.0.1', {}, 'x-forwarded-for')).toBe('10.0.0.1')
    expect(istemciAdresi('10.0.0.1', { 'x-forwarded-for': 'herhangi-bir-sey' }, 'x-forwarded-for')).toBe('10.0.0.1')
    expect(istemciAdresi('10.0.0.1', { 'x-forwarded-for': '' }, 'x-forwarded-for')).toBe('10.0.0.1')
  })
})

// nuxt-security'nin hız sınırlayıcısı adresi bu çağrıyla alır: getRequestIP(event, { xForwardedFor: true })
describe('getRequestIP (gerçek HTTP sunucusu, server/middleware/istemciAdresi.ts gibi)', () => {
  let sunucu: Server
  let port: number
  let baslik: string | undefined

  beforeAll(async () => {
    const app = createApp()
    app.use(defineEventHandler((event) => {
      const { socket, headers } = event.node.req
      const adres = istemciAdresi(socket.remoteAddress, headers, baslik)
      if (adres) event.context.clientAddress = adres
    }))
    app.use(defineEventHandler(event => ({ ip: getRequestIP(event, { xForwardedFor: true }) })))
    sunucu = createServer(toNodeListener(app))
    await new Promise<void>(r => sunucu.listen(0, '127.0.0.1', r))
    port = (sunucu.address() as AddressInfo).port
  })

  afterAll(() => new Promise<void>(r => sunucu.close(() => r())))

  const ipSor = (basliklar: Record<string, string>) => new Promise<string>((resolve, reject) => {
    request({ host: '127.0.0.1', port, path: '/', headers: basliklar, agent: false }, (y) => {
      let g = ''
      y.on('data', p => g += p).on('end', () => resolve(JSON.parse(g).ip))
    }).on('error', reject).end()
  })

  it('istemcinin yazdığı X-Forwarded-For hız sınırı adresini değiştiremez', async () => {
    baslik = undefined
    expect(await ipSor({ 'x-forwarded-for': '1.2.3.4' })).toBe('127.0.0.1')
    expect(await ipSor({ 'x-forwarded-for': '5.6.7.8' })).toBe('127.0.0.1')
  })

  it('güvenilir başlık tanımlıysa o kullanılır', async () => {
    baslik = 'x-forwarded-for'
    expect(await ipSor({ 'x-forwarded-for': '9.9.9.9, 203.0.113.7' })).toBe('203.0.113.7')
  })
})
