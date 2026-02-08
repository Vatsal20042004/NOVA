import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCartStore } from '../stores/cartStore';
import { ordersApi, paymentsApi } from '../api';
import { formatPrice, FREE_SHIPPING_THRESHOLD_INR, SHIPPING_CHARGE_INR } from '../utils/currency';
import toast from 'react-hot-toast';

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { items, getTotal, clearCart } = useCartStore();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    fullName: '',
    email: '',
    address: '',
    city: '',
    state: '',
    zipCode: '',
    country: 'India',
  });

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (items.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    setLoading(true);
    try {
      // Create order
      const shippingAddress = `${formData.fullName}\n${formData.address}\n${formData.city}, ${formData.state} ${formData.zipCode}\n${formData.country}`;
      
      const orderResponse = await ordersApi.create({
        items: items.map((item) => ({
          product_id: item.product_id,
          quantity: item.quantity,
        })),
        shipping_address: shippingAddress,
      });

      // Process payment
      await paymentsApi.process(orderResponse.data.id);

      // Clear cart and redirect
      clearCart();
      toast.success('Order placed successfully!');
      navigate('/orders');
    } catch (error: unknown) {
      const err = error as { response?: { data?: { message?: string } } };
      toast.error(err.response?.data?.message || 'Failed to place order');
    } finally {
      setLoading(false);
    }
  };

  if (items.length === 0) {
    navigate('/cart');
    return null;
  }

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Checkout</h1>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Shipping Information */}
          <div className="lg:col-span-2 space-y-6">
            <div className="card">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                Shipping Information
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Full Name
                  </label>
                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    required
                    className="input"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="input"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Address
                  </label>
                  <input
                    type="text"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    required
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    City
                  </label>
                  <input
                    type="text"
                    name="city"
                    value={formData.city}
                    onChange={handleChange}
                    required
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    State / Province
                  </label>
                  <input
                    type="text"
                    name="state"
                    value={formData.state}
                    onChange={handleChange}
                    required
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    ZIP / Postal Code
                  </label>
                  <input
                    type="text"
                    name="zipCode"
                    value={formData.zipCode}
                    onChange={handleChange}
                    required
                    className="input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Country
                  </label>
                  <select
                    name="country"
                    value={formData.country}
                    onChange={handleChange}
                    className="input"
                  >
                    <option>United States</option>
                    <option>Canada</option>
                    <option>United Kingdom</option>
                    <option>Australia</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Payment (Simulated) */}
            <div className="card">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                Payment Method
              </h2>
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-yellow-800">
                  <strong>Demo Mode:</strong> Payment is simulated. No real
                  charges will be made.
                </p>
              </div>
            </div>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="card sticky top-24">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                Order Summary
              </h2>

              {/* Items */}
              <div className="space-y-4 mb-6">
                {items.map((item) => (
                  <div
                    key={item.product_id}
                    className="flex justify-between text-sm"
                  >
                    <span className="text-gray-600">
                      {item.product.name} x {item.quantity}
                    </span>
                    <span className="text-gray-900">
                      {formatPrice(item.product.price * item.quantity)}
                    </span>
                  </div>
                ))}
              </div>

              <div className="border-t border-gray-200 pt-4 space-y-2">
                <div className="flex justify-between text-gray-600">
                  <span>Subtotal</span>
                  <span>{formatPrice(getTotal())}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Shipping</span>
                  <span>{getTotal() >= FREE_SHIPPING_THRESHOLD_INR ? 'Free' : formatPrice(SHIPPING_CHARGE_INR)}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Tax (8%)</span>
                  <span>{formatPrice(getTotal() * 0.08)}</span>
                </div>
                <div className="border-t border-gray-200 pt-2 flex justify-between">
                  <span className="text-lg font-bold text-gray-900">Total</span>
                  <span className="text-lg font-bold text-gray-900">
                    {formatPrice(
                      getTotal() +
                      (getTotal() >= FREE_SHIPPING_THRESHOLD_INR ? 0 : SHIPPING_CHARGE_INR) +
                      getTotal() * 0.08
                    )}
                  </span>
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full mt-6"
              >
                {loading ? 'Processing...' : 'Place Order'}
              </button>
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
