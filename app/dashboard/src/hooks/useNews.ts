// src/hooks/useNews.ts
import { useState, useEffect, useCallback } from 'react'

import { newsApi } from '@/service/newsApi'
import type { Article } from '@/service/newsApi'

export type NewsFilter =
  | { type: 'all' }
  | { type: 'category';  value: string }
  | { type: 'sentiment'; value: string }

export function useNews() {
  const [articles, setArticles] = useState<Article[]>([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState<string | null>(null)
  const [filter, setFilter]     = useState<NewsFilter>({ type: 'all' })

 const load = useCallback(async () => {
  setLoading(true)
  setError(null)

  try {
    let res: Article[]

    if (filter.type === 'all')
      res = await newsApi.getAll()
    else if (filter.type === 'category')
      res = await newsApi.getByCategory(filter.value)
    else
      res = await newsApi.getBySentiment(filter.value)

    setArticles(res)
  } catch (e) {
    setError(e instanceof Error ? e.message : 'Gagal memuat berita')
  } finally {
    setLoading(false)
  }
}, [filter])

  useEffect(() => { load() }, [load])

  return { articles, loading, error, filter, setFilter, refresh: load }
}
