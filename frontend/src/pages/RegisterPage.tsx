import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { SparklesIcon, UserIcon, EnvelopeIcon, LockClosedIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../stores/authStore';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const navigate = useNavigate();
  const register = useAuthStore((state) => state.register);
  const isLoading = useAuthStore((state) => state.isLoading);

  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    password: '',
    confirmPassword: '',
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      toast.error('Password must be at least 8 characters');
      return;
    }
    if (!/[A-Z]/.test(formData.password)) {
      toast.error('Password must contain at least one uppercase letter');
      return;
    }
    if (!/[a-z]/.test(formData.password)) {
      toast.error('Password must contain at least one lowercase letter');
      return;
    }
    if (!/\d/.test(formData.password)) {
      toast.error('Password must contain at least one digit');
      return;
    }

    try {
      await register(formData.email, formData.password, formData.fullName);
      toast.success('Account created successfully!');
      navigate('/');
    } catch (error: any) {
      console.error('Registration error:', error);
      let errorMsg = 'Registration failed. Email may already be registered.';

      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          // Handle Pydantic validation errors
          errorMsg = error.response.data.detail
            .map((err: any) => err.msg.replace('Value error, ', ''))
            .join('. ');
        } else {
          errorMsg = error.response.data.detail;
        }
      } else if (error.response?.data?.message) {
        errorMsg = error.response.data.message;
      }

      toast.error(errorMsg);
    }
  };

  return (
    <div className="min-h-[70vh] flex items-center justify-center py-12">
      <div className="w-full max-w-md">
        <div className="glass p-8 rounded-3xl shadow-soft animate-fade-in">
          <div className="text-center mb-10">
            <div className="w-16 h-16 bg-gradient-to-br from-accent-500 to-accent-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-accent-500/30">
              <SparklesIcon className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Join Luxe</h1>
            <p className="text-gray-600 mt-2">
              Create your account and start shopping
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Full Name
              </label>
              <div className="relative">
                <UserIcon className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  name="fullName"
                  value={formData.fullName}
                  onChange={handleChange}
                  required
                  className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all bg-white/50"
                  placeholder="John Doe"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email
              </label>
              <div className="relative">
                <EnvelopeIcon className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleChange}
                  required
                  className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all bg-white/50"
                  placeholder="you@example.com"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Password
              </label>
              <div className="relative">
                <LockClosedIcon className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  name="password"
                  value={formData.password}
                  onChange={handleChange}
                  required
                  minLength={8}
                  className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all bg-white/50"
                  placeholder="At least 8 characters"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Confirm Password
              </label>
              <div className="relative">
                <ShieldCheckIcon className="w-5 h-5 absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  className="w-full pl-12 pr-4 py-4 rounded-2xl border border-gray-200 focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 transition-all bg-white/50"
                  placeholder="Confirm your password"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn-primary w-full py-4 text-lg"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating account...
                </span>
              ) : 'Create Account'}
            </button>
          </form>

          <p className="text-center mt-8 text-gray-600">
            Already have an account?{' '}
            <Link to="/login" className="text-primary-600 hover:text-primary-700 font-semibold hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
