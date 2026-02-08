import { Link, Outlet } from 'react-router-dom';
import { ShoppingCartIcon, UserIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../stores/authStore';
import { useCartStore } from '../stores/cartStore';

export default function Layout() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const items = useCartStore((state) => state.items);
  const itemCount = items.reduce((acc, item) => acc + item.quantity, 0);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="glass sticky top-0 z-50 shadow-soft">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-18 py-4">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-lg shadow-primary-500/30 group-hover:scale-110 transition-transform">
                <SparklesIcon className="w-6 h-6 text-white" />
              </div>
              <span className="text-2xl font-bold gradient-text">
                Nova
              </span>
            </Link>

            {/* Navigation */}
            <nav className="hidden md:flex items-center space-x-8">
              <Link
                to="/products"
                className="text-gray-600 hover:text-primary-600 font-medium transition-colors relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary-500 hover:after:w-full after:transition-all"
              >
                Products
              </Link>
              <Link
                to="/categories"
                className="text-gray-600 hover:text-primary-600 font-medium transition-colors relative after:absolute after:bottom-0 after:left-0 after:w-0 after:h-0.5 after:bg-primary-500 hover:after:w-full after:transition-all"
              >
                Categories
              </Link>
            </nav>

            {/* Right side */}
            <div className="flex items-center space-x-3">
              {/* Cart */}
              <Link
                to="/cart"
                className="relative p-3 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-xl transition-all"
              >
                <ShoppingCartIcon className="h-6 w-6" />
                {itemCount > 0 && (
                  <span className="absolute top-1 right-1 bg-gradient-to-r from-accent-500 to-accent-600 text-white text-xs font-bold rounded-full h-5 w-5 flex items-center justify-center shadow-lg animate-pulse-slow">
                    {itemCount}
                  </span>
                )}
              </Link>

              {/* Auth */}
              {isAuthenticated ? (
                <div className="flex items-center space-x-3">
                  <Link
                    to="/orders"
                    className="text-gray-600 hover:text-primary-600 font-medium px-3 py-2 hover:bg-primary-50 rounded-xl transition-all"
                  >
                    Orders
                  </Link>
                  {user?.role === 'admin' && (
                    <Link
                      to="/admin"
                      className="text-gray-600 hover:text-primary-600 font-medium px-3 py-2 hover:bg-primary-50 rounded-xl transition-all"
                    >
                      Admin
                    </Link>
                  )}
                  <div className="relative group">
                    <button className="flex items-center gap-2 p-2 pl-3 text-gray-600 hover:text-primary-600 bg-gray-50 hover:bg-primary-50 rounded-xl transition-all">
                      <span className="hidden md:block font-medium">
                        {user?.full_name || 'Account'}
                      </span>
                      <div className="w-8 h-8 bg-gradient-to-br from-primary-400 to-primary-600 rounded-lg flex items-center justify-center">
                        <UserIcon className="h-4 w-4 text-white" />
                      </div>
                    </button>
                    {/* Dropdown */}
                    <div className="absolute right-0 mt-2 w-56 glass rounded-2xl shadow-lg border border-white/50 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all transform group-hover:translate-y-0 translate-y-2 p-2">
                      <Link
                        to="/profile"
                        className="flex items-center gap-3 px-4 py-3 text-gray-700 hover:bg-primary-50 hover:text-primary-700 rounded-xl transition-all"
                      >
                        <UserIcon className="w-5 h-5" />
                        Profile
                      </Link>
                      <button
                        onClick={logout}
                        className="flex items-center gap-3 w-full text-left px-4 py-3 text-gray-700 hover:bg-red-50 hover:text-red-600 rounded-xl transition-all"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                        </svg>
                        Logout
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center space-x-3">
                  <Link
                    to="/login"
                    className="text-gray-600 hover:text-primary-600 font-medium px-4 py-2 hover:bg-primary-50 rounded-xl transition-all"
                  >
                    Login
                  </Link>
                  <Link to="/register" className="btn-primary">
                    Get Started
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="glass border-t border-white/30 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            <div className="md:col-span-1">
              <Link to="/" className="flex items-center gap-2 mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center">
                  <SparklesIcon className="w-6 h-6 text-white" />
                </div>
                <span className="text-2xl font-bold gradient-text">Nova</span>
              </Link>
              <p className="text-gray-600 leading-relaxed">
                Premium shopping experience with curated products and exceptional service.
              </p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Shop</h4>
              <ul className="space-y-3">
                <li>
                  <Link to="/products" className="text-gray-600 hover:text-primary-600 transition-colors">
                    All Products
                  </Link>
                </li>
                <li>
                  <Link to="/products?featured=true" className="text-gray-600 hover:text-primary-600 transition-colors">
                    Featured
                  </Link>
                </li>
                <li>
                  <Link to="/products?sale=true" className="text-gray-600 hover:text-primary-600 transition-colors">
                    On Sale
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Account</h4>
              <ul className="space-y-3">
                <li>
                  <Link to="/profile" className="text-gray-600 hover:text-primary-600 transition-colors">
                    My Profile
                  </Link>
                </li>
                <li>
                  <Link to="/orders" className="text-gray-600 hover:text-primary-600 transition-colors">
                    Order History
                  </Link>
                </li>
                <li>
                  <Link to="/cart" className="text-gray-600 hover:text-primary-600 transition-colors">
                    Shopping Cart
                  </Link>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Support</h4>
              <ul className="space-y-3">
                <li className="text-gray-600">support@nova.com</li>
                <li className="text-gray-600">1-800-AURA</li>
                <li className="flex gap-3 mt-4">
                  <a href="#" className="w-10 h-10 bg-gray-100 hover:bg-primary-100 hover:text-primary-600 rounded-xl flex items-center justify-center transition-all">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M24 4.557c-.883.392-1.832.656-2.828.775 1.017-.609 1.798-1.574 2.165-2.724-.951.564-2.005.974-3.127 1.195-.897-.957-2.178-1.555-3.594-1.555-3.179 0-5.515 2.966-4.797 6.045-4.091-.205-7.719-2.165-10.148-5.144-1.29 2.213-.669 5.108 1.523 6.574-.806-.026-1.566-.247-2.229-.616-.054 2.281 1.581 4.415 3.949 4.89-.693.188-1.452.232-2.224.084.626 1.956 2.444 3.379 4.6 3.419-2.07 1.623-4.678 2.348-7.29 2.04 2.179 1.397 4.768 2.212 7.548 2.212 9.142 0 14.307-7.721 13.995-14.646.962-.695 1.797-1.562 2.457-2.549z" /></svg>
                  </a>
                  <a href="#" className="w-10 h-10 bg-gray-100 hover:bg-primary-100 hover:text-primary-600 rounded-xl flex items-center justify-center transition-all">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z" /></svg>
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-200/50 mt-12 pt-8 text-center">
            <p className="text-gray-500">&copy; 2026 Nova. Crafted with care.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
