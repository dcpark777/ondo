import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Ondo Dataset Readiness
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Score and improve your dataset readiness
        </p>
        <Link
          href="/datasets"
          className="inline-block bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition"
        >
          View Datasets
        </Link>
      </div>
    </div>
  )
}

