import { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { userApi } from '../api';
import toast from 'react-hot-toast';

export default function ProfilePage() {
  const { user, fetchProfile } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
  });

  useEffect(() => {
    if (user) {
      setFormData({
        full_name: user.full_name || '',
        email: user.email || '',
      });
    }
  }, [user]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await userApi.updateProfile({ full_name: formData.full_name });
      await fetchProfile();
      toast.success('Profile updated');
    } catch {
      toast.error('Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Profile</h1>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Full Name
            </label>
            <input
              type="text"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              className="input"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              name="email"
              value={formData.email}
              disabled
              className="input bg-gray-50"
            />
            <p className="text-sm text-gray-500 mt-1">
              Email cannot be changed
            </p>
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={loading}
              className="btn-primary"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>

      {/* Account Info */}
      <div className="card mt-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Account Info</h2>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between">
            <span className="text-gray-600">Member since</span>
            <span className="text-gray-900">
              {user?.created_at
                ? new Date(user.created_at).toLocaleDateString()
                : 'N/A'}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-600">Account status</span>
            <span className="text-green-600 font-medium">Active</span>
          </div>
        </div>
      </div>
    </div>
  );
}
