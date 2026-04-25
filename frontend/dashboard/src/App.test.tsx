import { fireEvent, render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'

vi.mock('@/features/dashboard/hooks/useDashboard', () => ({
  useDashboard: () => ({
    data: {
      summary: {
        total_keywords: 3,
        briefed_keywords: 1,
        articles: 1,
        published_articles: 0,
      },
      keywords: [
        {
          id: 'kw-1',
          term: 'restaurant food cost percentage',
          intent: 'commercial',
          trend: 'up',
          score: 76,
          volume: 400,
          difficulty: 32,
          has_brief: true,
          priority: 'high',
        },
      ],
      articles: [
        {
          id: 'art-1',
          title: 'Food Cost Guide',
          status: 'draft',
          file_path: '/tmp/article.md',
          published_url: null,
          created_at: '2026-04-24T00:00:00Z',
        },
      ],
      usage: [],
      paths: {
        database: '/tmp/seo.db',
        articles_dir: '/tmp/articles',
      },
    },
    loading: false,
    error: null,
    lastUpdated: new Date('2026-04-24T00:00:00Z'),
    refresh: vi.fn(),
  }),
}))

vi.mock('@/features/profiles/hooks/useProfiles', () => ({
  useProfiles: () => ({
    data: {
      active_profile: 'restaurant',
      profiles: [
        {
          slug: 'restaurant',
          site_name: 'Restaurant Ops',
          site_url: 'https://example.com',
          site_description: 'Restaurant analytics',
          is_default: false,
          site_config: {
            site_url: 'https://example.com',
            site_name: 'Restaurant Ops',
            site_description: '',
            target_audience: '',
            services: [],
            primary_language: 'en',
            blog_url: '',
            existing_articles: [],
            seed_keywords: [],
            target_persona: '',
            competitors: [],
            geographic_focus: [],
          },
          database_url: 'sqlite:////tmp/seo.db',
          keywords: 3,
          articles: 1,
          runs: 2,
          approved_noise: 1,
          approved_validity: 2,
          approved_legitimacy: 1,
        },
      ],
    },
    loading: false,
    error: null,
    refreshing: false,
    clearError: vi.fn(),
    refresh: vi.fn(),
    switchProfile: vi.fn(),
    createProfile: vi.fn(),
    updateProfile: vi.fn(),
    deleteProfile: vi.fn(),
  }),
}))

vi.mock('@/features/reviews/hooks/useTrainingReview', () => ({
  useTrainingReview: () => ({
    data: {
      profile: {
        slug: 'restaurant',
        site_name: 'Restaurant Ops',
        site_url: 'https://example.com',
        runs: 2,
        approved_noise: 1,
        approved_validity: 2,
        approved_legitimacy: 1,
      },
      approved: {
        noise: { keyword_phrases: [], secondary_phrases: [], domains: [] },
        validity: { keyword_phrases: [], secondary_phrases: [] },
        legitimacy: { domains: [] },
      },
      candidates: [],
    },
    loading: false,
    error: null,
    approving: false,
    refresh: vi.fn(),
    approve: vi.fn(),
  }),
}))

vi.mock('@/features/reviews/hooks/useFinalReview', () => ({
  useFinalReview: () => ({
    data: {
      summary: [],
      shared_valid_keywords: [],
      shared_trusted_domains: [],
      profiles: [],
    },
    loading: false,
    error: null,
    refresh: vi.fn(),
  }),
}))

vi.mock('@/features/validation/hooks/useValidateFreeAction', () => ({
  useValidateFreeAction: () => ({
    data: null,
    running: false,
    error: null,
    run: vi.fn(),
  }),
}))

vi.mock('@/features/keywords/hooks/useKeywordDetail', () => ({
  useKeywordDetail: () => ({
    data: null,
    loading: false,
    error: null,
  }),
}))

describe('App routing shell', () => {
  beforeEach(() => {
    window.history.pushState({}, '', '/overview')
  })

  it('renders the app shell and navigates between primary routes', () => {
    render(
      <BrowserRouter>
        <App />
      </BrowserRouter>,
    )

    expect(screen.getByText('Nichefinder')).toBeInTheDocument()
    expect(screen.getByText('Quick Actions')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('link', { name: /keyword explorer/i }))

    expect(screen.getByText('Keyword Queue')).toBeInTheDocument()
    expect(window.location.pathname).toBe('/explorer')
  })
})
