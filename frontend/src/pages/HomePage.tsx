import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, SparklesIcon, TruckIcon, ShieldCheckIcon, StarIcon } from '@heroicons/react/24/outline';
import ProductCard from '../components/ProductCard';
import { productsApi, recommendationsApi, newsletterApi } from '../api';
import { useAuthStore } from '../stores/authStore';
import type { Product } from '../types';
import toast from 'react-hot-toast';

export default function HomePage() {
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const isLoggedIn = useAuthStore((s) => !!s.accessToken);

  const handleSubscribe = async () => {
    if (!email) {
      toast.error('Please enter your email address');
      return;
    }
    if (!/\S+@\S+\.\S+/.test(email)) {
      toast.error('Please enter a valid email address');
      return;
    }

    setSubmitting(true);
    try {
      await newsletterApi.subscribe(email);
      toast.success('Check your inbox! Subscription successful.');
      setEmail('');
    } catch {
      toast.error('Failed to subscribe. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const [productsRes, recsRes] = await Promise.all([
          productsApi.list(1, 8),
          isLoggedIn
            ? recommendationsApi.getForMe(8).catch(() => ({ data: [] }))
            : productsApi.getRecommendationsFallback(8).catch(() => ({ data: [] })),
        ]);
        setFeaturedProducts(productsRes.data);
        setRecommendations(recsRes.data);
      } catch (error) {
        console.error('Failed to fetch products:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [isLoggedIn]);

  return (
    <div className="space-y-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 rounded-3xl"></div>
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')] opacity-50 rounded-3xl"></div>

        <div className="relative px-8 py-20 md:py-28 text-white">
          <div className="max-w-2xl animate-slide-up">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-6">
              <SparklesIcon className="w-4 h-4 text-accent-400" />
              <span className="text-sm font-medium">New Collection Available</span>
            </div>
            <h1 className="text-4xl md:text-6xl font-bold mb-6 leading-tight">
              Discover Premium <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-300 to-accent-500">Luxury Products</span>
            </h1>
            <p className="text-lg md:text-xl text-primary-100 mb-10 leading-relaxed">
              Curated collection of premium products with exceptional quality.
              Experience shopping reimagined.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link to="/products" className="group inline-flex items-center gap-2 bg-white text-primary-700 font-semibold px-8 py-4 rounded-2xl shadow-lg shadow-black/20 hover:shadow-xl hover:scale-105 transition-all">
                Browse Collection
                <ArrowRightIcon className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link
                to="/categories"
                className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 text-white font-semibold px-8 py-4 rounded-2xl hover:bg-white/20 transition-all"
              >
                Browse Categories
              </Link>
            </div>
          </div>
        </div>

        {/* Decorative elements */}
        <div className="absolute top-10 right-10 w-72 h-72 bg-accent-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-10 right-40 w-48 h-48 bg-primary-400/30 rounded-full blur-2xl"></div>
        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl"></div>
      </section>

      {/* Features */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card-hover group p-8">
          <div className="w-14 h-14 bg-gradient-to-br from-primary-100 to-primary-200 rounded-2xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
            <StarIcon className="w-7 h-7 text-primary-600" />
          </div>
          <h3 className="font-bold text-gray-900 text-lg mb-2">Premium Quality</h3>
          <p className="text-gray-600 leading-relaxed">Every product is handpicked and verified for exceptional quality standards.</p>
        </div>
        <div className="card-hover group p-8">
          <div className="w-14 h-14 bg-gradient-to-br from-accent-100 to-accent-200 rounded-2xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
            <TruckIcon className="w-7 h-7 text-accent-600" />
          </div>
          <h3 className="font-bold text-gray-900 text-lg mb-2">Express Delivery</h3>
          <p className="text-gray-600 leading-relaxed">Free express shipping on all orders over ₹5,000. Track your package in real-time.</p>
        </div>
        <div className="card-hover group p-8">
          <div className="w-14 h-14 bg-gradient-to-br from-green-100 to-green-200 rounded-2xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform">
            <ShieldCheckIcon className="w-7 h-7 text-green-600" />
          </div>
          <h3 className="font-bold text-gray-900 text-lg mb-2">Secure Checkout</h3>
          <p className="text-gray-600 leading-relaxed">Your data is encrypted and protected with enterprise-grade security.</p>
        </div>
      </section>

      {/* Featured Products */}
      <section>
        <div className="flex items-center justify-between mb-10">
          <div>
            <h2 className="text-3xl font-bold text-gray-900 mb-2">Featured Products</h2>
            <p className="text-gray-600">Handpicked selections for you</p>
          </div>
          <Link
            to="/products"
            className="group flex items-center gap-2 text-primary-600 hover:text-primary-700 font-semibold bg-primary-50 px-5 py-3 rounded-xl hover:bg-primary-100 transition-all"
          >
            View All
            <ArrowRightIcon className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="card-hover animate-pulse p-5">
                <div className="aspect-square bg-gradient-to-br from-gray-200 to-gray-100 rounded-2xl mb-4"></div>
                <div className="h-4 bg-gray-200 rounded-full w-3/4 mb-3"></div>
                <div className="h-4 bg-gray-200 rounded-full w-1/2"></div>
              </div>
            ))}
          </div>
        ) : featuredProducts.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {featuredProducts.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        ) : (
          <div className="text-center py-16 glass rounded-3xl">
            <SparklesIcon className="w-16 h-16 text-primary-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-700 mb-2">No Products Yet</h3>
            <p className="text-gray-500">Check back soon for new arrivals!</p>
          </div>
        )}
      </section>

      {/* Recommendations */}
      {recommendations.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-10">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 mb-2">Recommended for You</h2>
              <p className="text-gray-600">Based on your preferences</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {recommendations.slice(0, 4).map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </section>
      )}

      {/* CTA */}
      <section className="relative overflow-hidden rounded-3xl">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900"></div>
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PGNpcmNsZSBjeD0iMzAiIGN5PSIzMCIgcj0iMiIvPjwvZz48L2c+PC9zdmc+')]"></div>
        <div className="absolute top-0 right-0 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-72 h-72 bg-accent-500/10 rounded-full blur-3xl"></div>

        <div className="relative px-8 py-16 text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-6">
            <SparklesIcon className="w-4 h-4 text-accent-400" />
            <span className="text-sm font-medium text-white/90">Stay Updated</span>
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
            Join Our Exclusive Newsletter
          </h2>
          <p className="text-gray-400 mb-10 max-w-xl mx-auto text-lg">
            Subscribe to get special offers, free giveaways, and once-in-a-lifetime deals.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 max-w-lg mx-auto">
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="flex-1 px-6 py-4 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <button
              onClick={handleSubscribe}
              disabled={submitting}
              className="btn-primary whitespace-nowrap px-8 py-4 disabled:opacity-50"
            >
              {submitting ? 'Subscribing...' : 'Subscribe'}
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
