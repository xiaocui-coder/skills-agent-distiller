import { BrowserRouter, useLocation } from 'react-router-dom'
import { matchPath } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from './components/common/ErrorBoundary'
import { MainLayout } from './components/layout/MainLayout'
import { ChatPage } from './pages/ChatPage'
import { SkillsPage } from './pages/SkillsPage'
import { DistillerPage } from './pages/DistillerPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
})

const pages = [
  { paths: ['/', '/chat'], element: <ChatPage /> },
  { paths: ['/skills', '/skills/:name'], element: <SkillsPage /> },
  { paths: ['/distiller'], element: <DistillerPage /> },
]

function PageRouter() {
  const location = useLocation()

  return (
    <>
      {pages.map(({ paths, element }) => {
        const active = paths.some((p) => matchPath(p, location.pathname))
        return (
          <div key={paths[0]} className={active ? '' : 'hidden'}>
            {element}
          </div>
        )
      })}
    </>
  )
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MainLayout>
          <ErrorBoundary>
            <PageRouter />
          </ErrorBoundary>
        </MainLayout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
