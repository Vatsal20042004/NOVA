import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  CubeIcon,
  UsersIcon,
  ExclamationTriangleIcon,
  PencilIcon,
  TrashIcon,
  PlusIcon,
} from '@heroicons/react/24/outline';
import { productsApi, adminApi } from '../api';
import { formatPrice } from '../utils/currency';
import type { Product, User } from '../types';
import toast from 'react-hot-toast';

type Tab = 'overview' | 'users' | 'products';

export default function AdminDashboard() {
  const [tab, setTab] = useState<Tab>('overview');
  const [lowStock, setLowStock] = useState<{ product_id: number; available: number; is_low_stock: boolean }[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [productForm, setProductForm] = useState<{
    open: boolean;
    editingId: number | null;
    name: string;
    description: string;
    price: string;
    image_url: string;
    is_active: boolean;
    is_featured: boolean;
    initial_stock: string;
  }>({
    open: false,
    editingId: null,
    name: '',
    description: '',
    price: '',
    image_url: '',
    is_active: true,
    is_featured: false,
    initial_stock: '0',
  });

  const loadOverview = async () => {
    setLoading(true);
    try {
      const res = await adminApi.getLowStock(20);
      setLowStock(
        (res.data as unknown as { product_id: number; available: number; is_low_stock: boolean }[]) || []
      );
    } catch {
      toast.error('Failed to load low stock');
    } finally {
      setLoading(false);
    }
  };

  const loadUsers = async () => {
    setLoading(true);
    try {
      const res = await adminApi.listUsers(1, 50);
      setUsers(res.data || []);
    } catch {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const loadProducts = async () => {
    setLoading(true);
    try {
      const res = await productsApi.list(1, 100);
      setProducts(res.data || []);
    } catch {
      toast.error('Failed to load products');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (tab === 'overview') loadOverview();
    else if (tab === 'users') loadUsers();
    else if (tab === 'products') loadProducts();
  }, [tab]);

  const handleSetRole = async (userId: number, role: 'customer' | 'admin' | 'driver') => {
    try {
      await adminApi.setUserRole(userId, role);
      toast.success('Role updated');
      loadUsers();
    } catch {
      toast.error('Failed to update role');
    }
  };

  const handleDeactivate = async (userId: number) => {
    if (!confirm('Deactivate this user?')) return;
    try {
      await adminApi.deactivateUser(userId);
      toast.success('User deactivated');
      loadUsers();
    } catch {
      toast.error('Failed to deactivate');
    }
  };

  const openCreateProduct = () => {
    setProductForm({
      open: true,
      editingId: null,
      name: '',
      description: '',
      price: '',
      image_url: '',
      is_active: true,
      is_featured: false,
      initial_stock: '0',
    });
  };

  const openEditProduct = (p: Product) => {
    setProductForm({
      open: true,
      editingId: p.id,
      name: p.name,
      description: p.description || '',
      price: String(p.price),
      image_url: p.image_url || '',
      is_active: p.is_active ?? true,
      is_featured: false,
      initial_stock: '0',
    });
  };

  const saveProduct = async () => {
    const price = parseFloat(productForm.price);
    const initial_stock = parseInt(productForm.initial_stock, 10) || 0;
    if (!productForm.name || isNaN(price) || price <= 0) {
      toast.error('Name and valid price required');
      return;
    }
    try {
      if (productForm.editingId) {
        await productsApi.update(productForm.editingId, {
          name: productForm.name,
          description: productForm.description || undefined,
          price,
          image_url: productForm.image_url || undefined,
          is_active: productForm.is_active,
        });
        toast.success('Product updated');
      } else {
        await productsApi.create({
          name: productForm.name,
          description: productForm.description || undefined,
          price,
          image_url: productForm.image_url || undefined,
          is_active: productForm.is_active,
          is_featured: productForm.is_featured,
          initial_stock,
        });
        toast.success('Product created');
      }
      setProductForm((f) => ({ ...f, open: false }));
      loadProducts();
      loadOverview();
    } catch (e: unknown) {
      const msg = e && typeof e === 'object' && 'response' in e && (e as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      toast.error(msg || 'Failed to save product');
    }
  };

  const deleteProduct = async (id: number) => {
    if (!confirm('Delete this product?')) return;
    try {
      await productsApi.delete(id);
      toast.success('Product deleted');
      loadProducts();
      loadOverview();
    } catch {
      toast.error('Failed to delete product');
    }
  };

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Overview', icon: ExclamationTriangleIcon },
    { id: 'users', label: 'Users', icon: UsersIcon },
    { id: 'products', label: 'Products', icon: CubeIcon },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600 mt-1">Manage users, products, and inventory.</p>
      </div>

      <div className="flex gap-2 border-b border-gray-200">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={`flex items-center gap-2 px-4 py-3 font-medium border-b-2 -mb-px transition-colors ${
              tab === id
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <Icon className="w-5 h-5" />
            {label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="space-y-6">
          <section className="card-hover p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Low Stock</h2>
            {loading ? (
              <p className="text-gray-500">Loading...</p>
            ) : lowStock.length === 0 ? (
              <p className="text-gray-500">No low stock items.</p>
            ) : (
              <ul className="space-y-2">
                {lowStock.map((item) => (
                  <li key={item.product_id} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-0">
                    <Link to={`/products/${item.product_id}`} className="text-primary-600 hover:underline">
                      Product #{item.product_id}
                    </Link>
                    <span className="text-amber-600 font-medium">Available: {item.available}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      )}

      {tab === 'users' && (
        <section className="card-hover overflow-hidden">
          {loading ? (
            <div className="p-8 text-gray-500">Loading users...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Active</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.email}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{u.full_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <select
                          value={u.role}
                          onChange={(e) => handleSetRole(u.id, e.target.value as 'customer' | 'admin' | 'driver')}
                          className="text-sm border border-gray-300 rounded-lg px-2 py-1"
                        >
                          <option value="customer">Customer</option>
                          <option value="admin">Admin</option>
                          <option value="driver">Driver</option>
                        </select>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{u.is_active ? 'Yes' : 'No'}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        {u.is_active && (
                          <button
                            onClick={() => handleDeactivate(u.id)}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
                          >
                            Deactivate
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {tab === 'products' && (
        <section className="space-y-4">
          <div className="flex justify-end">
            <button onClick={openCreateProduct} className="btn-primary flex items-center gap-2">
              <PlusIcon className="w-5 h-5" />
              Add Product
            </button>
          </div>
          <div className="card-hover overflow-hidden">
            {loading ? (
              <div className="p-8 text-gray-500">Loading products...</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Active</th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {products.map((p) => (
                      <tr key={p.id}>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            {p.image_url ? (
                              <img src={p.image_url} alt="" className="w-10 h-10 rounded object-cover" />
                            ) : (
                              <div className="w-10 h-10 rounded bg-gray-100 flex items-center justify-center">
                                <CubeIcon className="w-5 h-5 text-gray-400" />
                              </div>
                            )}
                            <div>
                              <Link to={`/products/${p.id}`} className="text-primary-600 hover:underline font-medium">
                                {p.name}
                              </Link>
                              <p className="text-xs text-gray-500">#{p.id}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm">{formatPrice(Number(p.price))}</td>
                        <td className="px-6 py-4 text-sm">{p.inventory?.available ?? '—'}</td>
                        <td className="px-6 py-4 text-sm">{p.is_active ? 'Yes' : 'No'}</td>
                        <td className="px-6 py-4 text-right flex justify-end gap-2">
                          <button
                            onClick={() => openEditProduct(p)}
                            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
                            title="Edit"
                          >
                            <PencilIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => deleteProduct(p.id)}
                            className="p-2 text-red-600 hover:bg-red-50 rounded-lg"
                            title="Delete"
                          >
                            <TrashIcon className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>
      )}

      {productForm.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">
              {productForm.editingId ? 'Edit Product' : 'Create Product'}
            </h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name *</label>
                <input
                  type="text"
                  value={productForm.name}
                  onChange={(e) => setProductForm((f) => ({ ...f, name: e.target.value }))}
                  className="input-field w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={productForm.description}
                  onChange={(e) => setProductForm((f) => ({ ...f, description: e.target.value }))}
                  className="input-field w-full"
                  rows={3}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price *</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={productForm.price}
                  onChange={(e) => setProductForm((f) => ({ ...f, price: e.target.value }))}
                  className="input-field w-full"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Image URL</label>
                <input
                  type="url"
                  value={productForm.image_url}
                  onChange={(e) => setProductForm((f) => ({ ...f, image_url: e.target.value }))}
                  className="input-field w-full"
                />
              </div>
              {!productForm.editingId && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Initial stock</label>
                  <input
                    type="number"
                    min="0"
                    value={productForm.initial_stock}
                    onChange={(e) => setProductForm((f) => ({ ...f, initial_stock: e.target.value }))}
                    className="input-field w-full"
                  />
                </div>
              )}
              <div className="flex gap-4">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={productForm.is_active}
                    onChange={(e) => setProductForm((f) => ({ ...f, is_active: e.target.checked }))}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700">Active</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={productForm.is_featured}
                    onChange={(e) => setProductForm((f) => ({ ...f, is_featured: e.target.checked }))}
                    className="rounded border-gray-300"
                  />
                  <span className="text-sm text-gray-700">Featured</span>
                </label>
              </div>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={saveProduct} className="btn-primary flex-1">
                {productForm.editingId ? 'Update' : 'Create'}
              </button>
              <button
                onClick={() => setProductForm((f) => ({ ...f, open: false }))}
                className="px-4 py-2 border border-gray-300 rounded-xl text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
