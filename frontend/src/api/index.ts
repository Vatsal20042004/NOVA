import api from './client';
import type {
  ApiResponse,
  PaginatedResponse,
  User,
  Product,
  Category,
  Order,
  Payment,
  LoginResponse,
  RegisterData,
  CreateOrderData,
  Delivery,
  DeliveryStatus
} from '../types';

// Auth API
export const authApi = {
  register: async (data: RegisterData): Promise<ApiResponse<User>> => {
    const response = await api.post('/auth/register', data);
    return { success: true, data: response.data };
  },

  login: async (email: string, password: string): Promise<LoginResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);

    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<LoginResponse> => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },

  logout: async (): Promise<void> => {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore logout errors
    }
  },
};

// User API
export const userApi = {
  getProfile: async (): Promise<ApiResponse<User>> => {
    const response = await api.get('/users/me');
    return { success: true, data: response.data };
  },

  updateProfile: async (data: Partial<User>): Promise<ApiResponse<User>> => {
    const response = await api.put('/users/me', data);
    return { success: true, data: response.data };
  },
};

// Products API
export const productsApi = {
  list: async (page = 1, limit = 12): Promise<PaginatedResponse<Product>> => {
    const response = await api.get('/products', { params: { page, limit } });
    // Map backend response to frontend expected format
    const backendData = response.data;
    return {
      success: true,
      data: backendData.products || [],
      total: backendData.total || 0,
      page: backendData.page || 1,
      limit: backendData.per_page || limit,
    };
  },

  get: async (id: number): Promise<ApiResponse<Product>> => {
    const response = await api.get(`/products/${id}`);
    return { success: true, data: response.data };
  },

  search: async (query: string): Promise<ApiResponse<Product[]>> => {
    const response = await api.get('/products/search', { params: { q: query } });
    return { success: true, data: response.data.products || [] };
  },

  /** Fallback: list products when recommendations API not used (e.g. anonymous) */
  getRecommendationsFallback: async (limit = 8): Promise<ApiResponse<Product[]>> => {
    const response = await api.get('/products', { params: { limit, page: 1 } });
    const backendData = response.data;
    return {
      success: true,
      data: backendData.products || [],
    };
  },

  getSimilar: async (productId: number): Promise<ApiResponse<Product[]>> => {
    const response = await api.get('/products', { params: { limit: 4 } });
    return { success: true, data: response.data.products || [] };
  },

  create: async (data: { name: string; description?: string; price: number; discount_percent?: number; image_url?: string; is_active?: boolean; is_featured?: boolean; slug?: string; category_ids?: number[]; initial_stock?: number }): Promise<ApiResponse<Product>> => {
    const response = await api.post('/products', data);
    return { success: true, data: response.data };
  },

  update: async (id: number, data: Partial<{ name: string; description: string; price: number; discount_percent: number; image_url: string; is_active: boolean; is_featured: boolean; category_ids: number[] }>): Promise<ApiResponse<Product>> => {
    const response = await api.put(`/products/${id}`, data);
    return { success: true, data: response.data };
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/products/${id}`);
  },
};

// Recommendations API (uses real co-occurrence endpoints; requires auth for /me)
export const recommendationsApi = {
  getForMe: async (limit = 8): Promise<ApiResponse<Product[]>> => {
    const response = await api.get('/recommendations/me', { params: { limit } });
    const list = Array.isArray(response.data) ? response.data : [];
    return { success: true, data: list.map(briefToProduct) };
  },

  getSimilar: async (productId: number, limit = 4): Promise<ApiResponse<Product[]>> => {
    const response = await api.get(`/recommendations/product/${productId}/similar`, { params: { limit } });
    const list = Array.isArray(response.data) ? response.data : [];
    return { success: true, data: list.map(briefToProduct) };
  },

  getAlsoBought: async (productId: number, limit = 4): Promise<ApiResponse<Product[]>> => {
    const response = await api.get(`/recommendations/product/${productId}/also-bought`, { params: { limit } });
    const list = Array.isArray(response.data) ? response.data : [];
    return { success: true, data: list.map(briefToProduct) };
  },
};

function briefToProduct(b: { id: number; name: string; slug?: string; price?: number; effective_price?: number; image_url?: string; average_rating?: number; review_count?: number; is_in_stock?: boolean }): Product {
  const price = b.effective_price != null ? Number(b.effective_price) : (b.price != null ? Number(b.price) : 0);
  return {
    id: b.id,
    name: b.name,
    description: '',
    price,
    sku: b.slug || `product-${b.id}`,
    image_url: b.image_url,
    is_active: true,
    categories: [],
    inventory: { product_id: b.id, quantity: 0, reserved: 0, available: b.is_in_stock ? 1 : 0 },
    created_at: '',
  };
}

// Categories API
export const categoriesApi = {
  list: async (): Promise<ApiResponse<Category[]>> => {
    const response = await api.get('/categories');
    return { success: true, data: response.data || [] };
  },

  get: async (id: number): Promise<ApiResponse<Category>> => {
    const response = await api.get(`/categories/${id}`);
    return { success: true, data: response.data };
  },
};

// Orders API
export const ordersApi = {
  create: async (data: CreateOrderData): Promise<ApiResponse<Order>> => {
    const response = await api.post('/orders', data);
    return { success: true, data: response.data };
  },

  list: async (): Promise<ApiResponse<Order[]>> => {
    const response = await api.get('/orders');
    return { success: true, data: response.data.orders || response.data || [] };
  },

  get: async (id: number): Promise<ApiResponse<Order>> => {
    const response = await api.get(`/orders/${id}`);
    return { success: true, data: response.data };
  },

  cancel: async (id: number): Promise<ApiResponse<Order>> => {
    const response = await api.post(`/orders/${id}/cancel`);
    return { success: true, data: response.data };
  },
};

// Payments API
export const paymentsApi = {
  process: async (orderId: number): Promise<ApiResponse<Payment>> => {
    const response = await api.post(`/payments/${orderId}/process`);
    return response.data;
  },

  getStatus: async (paymentId: number): Promise<ApiResponse<Payment>> => {
    const response = await api.get(`/payments/${paymentId}`);
    return response.data;
  },
};

// Deliveries API
export const deliveriesApi = {
  getMyDeliveries: async (): Promise<ApiResponse<Delivery[]>> => {
    const response = await api.get('/deliveries/mine');
    return { success: true, data: response.data };
  },

  updateStatus: async (id: number, status: DeliveryStatus, location?: string): Promise<ApiResponse<Delivery>> => {
    const response = await api.patch(`/deliveries/${id}/status`, { status, current_location: location });
    return { success: true, data: response.data };
  },

  get: async (id: number): Promise<ApiResponse<Delivery>> => {
    const response = await api.get(`/deliveries/${id}`);
    return { success: true, data: response.data };
  }
};

// Newsletter API
export const newsletterApi = {
  subscribe: async (email: string): Promise<ApiResponse<any>> => {
    const response = await api.post('/newsletter/subscribe', { email });
    return { success: true, data: response.data };
  },
};

// Admin API (requires admin role)
export const adminApi = {
  listUsers: async (page = 1, perPage = 20, role?: string): Promise<ApiResponse<User[]>> => {
    const params: Record<string, number | string> = { page, per_page: perPage };
    if (role) params.role = role;
    const response = await api.get('/admin/users', { params });
    return { success: true, data: Array.isArray(response.data) ? response.data : [] };
  },

  setUserRole: async (userId: number, role: 'customer' | 'admin' | 'driver'): Promise<ApiResponse<User>> => {
    const response = await api.put(`/admin/users/${userId}/role`, null, { params: { role } });
    return { success: true, data: response.data };
  },

  deactivateUser: async (userId: number): Promise<ApiResponse<User>> => {
    const response = await api.post(`/admin/users/${userId}/deactivate`);
    return { success: true, data: response.data };
  },

  getLowStock: async (limit = 50): Promise<ApiResponse<{ id: number; product_id: number; quantity: number; reserved: number; available: number; is_low_stock: boolean }[]>> => {
    const response = await api.get('/admin/inventory/low-stock', { params: { limit } });
    return { success: true, data: response.data || [] };
  },

  updateOrderStatus: async (orderId: number, orderStatus: string, trackingNumber?: string): Promise<ApiResponse<Order>> => {
    const params: Record<string, string> = { order_status: orderStatus };
    if (trackingNumber) params.tracking_number = trackingNumber;
    const response = await api.put(`/admin/orders/${orderId}/status`, null, { params });
    return { success: true, data: response.data };
  },
};
