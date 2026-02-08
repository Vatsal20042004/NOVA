// API Types

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  role: 'customer' | 'admin' | 'driver';
  created_at: string;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  sku: string;
  image_url?: string;
  is_active: boolean;
  categories: Category[];
  inventory?: Inventory;
  created_at: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  description?: string;
  parent_id?: number;
}

export interface Inventory {
  product_id: number;
  quantity: number;
  reserved: number;
  available: number;
}

export interface CartItem {
  product_id: number;
  product: Product;
  quantity: number;
}

export interface Order {
  id: number;
  order_number: string;
  user_id: number;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  total_amount: number;
  shipping_address: string;
  items: OrderItem[];
  delivery?: Delivery;
  created_at: string;
}

export interface OrderItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

export interface Payment {
  id: number;
  order_id: number;
  amount: number;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
  transaction_id?: string;
}

export type DeliveryStatus = 'assigned' | 'picked_up' | 'in_transit' | 'delivered' | 'failed';

export interface Delivery {
  id: number;
  order_id: number;
  driver_id: number;
  status: DeliveryStatus;
  current_location?: string;
  proof_of_delivery?: string;
  delivery_notes?: string;
  picked_up_at?: string;
  delivered_at?: string;
  created_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data: T;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  limit: number;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginData {
  username: string;
  password: string;
}

export interface CreateOrderData {
  items: { product_id: number; quantity: number }[];
  shipping_address: string;
}
