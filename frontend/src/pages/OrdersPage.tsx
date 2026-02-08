import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ordersApi } from '../api';
import { formatPrice } from '../utils/currency';
import type { Order } from '../types';
import toast from 'react-hot-toast';

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800',
  confirmed: 'bg-blue-100 text-blue-800',
  shipped: 'bg-purple-100 text-purple-800',
  delivered: 'bg-green-100 text-green-800',
  cancelled: 'bg-red-100 text-red-800',
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchOrders() {
      try {
        const response = await ordersApi.list();
        setOrders(response.data);
      } catch (error) {
        console.error('Failed to fetch orders:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchOrders();
  }, []);

  const handleCancel = async (orderId: number) => {
    if (!confirm('Are you sure you want to cancel this order?')) return;

    try {
      await ordersApi.cancel(orderId);
      setOrders((prev) =>
        prev.map((order) =>
          order.id === orderId ? { ...order, status: 'cancelled' } : order
        )
      );
      toast.success('Order cancelled');
    } catch {
      toast.error('Failed to cancel order');
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="card animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
          </div>
        ))}
      </div>
    );
  }

  if (orders.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-gray-400 mb-4">
          <svg
            className="w-24 h-24 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
            />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">No orders yet</h2>
        <p className="text-gray-600 mb-8">
          Start shopping to see your orders here.
        </p>
        <Link to="/products" className="btn-primary">
          Browse Products
        </Link>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">My Orders</h1>

      <div className="space-y-6">
        {orders.map((order) => (
          <div key={order.id} className="card">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  Order #{order.order_number}
                </h2>
                <p className="text-sm text-gray-500">
                  Placed on {new Date(order.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${statusColors[order.status] || 'bg-gray-100 text-gray-800'
                    }`}
                >
                  {order.status}
                </span>
                {order.status === 'pending' && (
                  <button
                    onClick={() => handleCancel(order.id)}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </div>

            {/* Items */}
            <div className="border-t border-gray-100 pt-4">
              <div className="space-y-3">
                {order.items.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center justify-between"
                  >
                    <div>
                      <p className="font-medium text-gray-900">
                        {item.product_name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {formatPrice(Number(item.unit_price))} x {item.quantity}
                      </p>
                    </div>
                    <p className="font-medium text-gray-900">
                      {formatPrice(Number(item.total_price))}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="border-t border-gray-100 mt-4 pt-4 flex justify-between items-center">
              <p className="text-sm text-gray-500">
                Shipping to: {order.shipping_address.split('\n')[0]}
              </p>
              <p className="text-lg font-bold text-gray-900">
                Total: {formatPrice(Number(order.total_amount))}
              </p>
            </div>

            {/* Delivery Status */}
            {order.delivery && (
              <div className="bg-blue-50 border-t border-blue-100 p-4 mt-4 -mx-6 -mb-6 rounded-b-lg">
                <h3 className="font-semibold text-blue-900 mb-2">Delivery Update</h3>
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-sm text-blue-800">
                      <span className="font-medium">Status:</span> {order.delivery.status.replace('_', ' ').toUpperCase()}
                    </p>
                    {order.delivery.current_location && (
                      <p className="text-sm text-blue-800">
                        <span className="font-medium">Location:</span> {order.delivery.current_location}
                      </p>
                    )}
                    {order.delivery.delivery_notes && (
                      <p className="text-sm text-blue-800 mt-1">
                        <span className="font-medium">Note:</span> {order.delivery.delivery_notes}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
