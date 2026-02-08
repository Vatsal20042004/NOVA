import { Link } from 'react-router-dom';
import { TrashIcon, MinusIcon, PlusIcon } from '@heroicons/react/24/outline';
import { useCartStore } from '../stores/cartStore';
import { formatPrice, FREE_SHIPPING_THRESHOLD_INR, SHIPPING_CHARGE_INR } from '../utils/currency';

export default function CartPage() {
  const { items, removeItem, updateQuantity, getTotal, clearCart } = useCartStore();

  if (items.length === 0) {
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
              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"
            />
          </svg>
        </div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Your cart is empty
        </h2>
        <p className="text-gray-600 mb-8">
          Looks like you haven't added any items yet.
        </p>
        <Link to="/products" className="btn-primary">
          Continue Shopping
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Shopping Cart</h1>
        <button
          onClick={clearCart}
          className="text-red-600 hover:text-red-700 font-medium"
        >
          Clear Cart
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Cart Items */}
        <div className="lg:col-span-2 space-y-4">
          {items.map((item) => (
            <div
              key={item.product_id}
              className="card flex items-center space-x-4"
            >
              {/* Image */}
              <div className="w-24 h-24 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                {item.product.image_url ? (
                  <img
                    src={item.product.image_url}
                    alt={item.product.name}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400">
                    <svg
                      className="w-8 h-8"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={1}
                        d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                      />
                    </svg>
                  </div>
                )}
              </div>

              {/* Info */}
              <div className="flex-1 min-w-0">
                <Link
                  to={`/products/${item.product_id}`}
                  className="font-semibold text-gray-900 hover:text-primary-600 line-clamp-1"
                >
                  {item.product.name}
                </Link>
                <p className="text-primary-600 font-medium">
                  {formatPrice(Number(item.product.price))}
                </p>
              </div>

              {/* Quantity */}
              <div className="flex items-center border border-gray-300 rounded-lg">
                <button
                  onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                  className="p-2 hover:bg-gray-50"
                >
                  <MinusIcon className="h-4 w-4" />
                </button>
                <span className="px-3 font-medium">{item.quantity}</span>
                <button
                  onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                  className="p-2 hover:bg-gray-50"
                >
                  <PlusIcon className="h-4 w-4" />
                </button>
              </div>

              {/* Total */}
              <div className="text-right w-24">
                <p className="font-semibold text-gray-900">
                  {formatPrice(Number(item.product.price) * item.quantity)}
                </p>
              </div>

              {/* Remove */}
              <button
                onClick={() => removeItem(item.product_id)}
                className="p-2 text-gray-400 hover:text-red-600"
              >
                <TrashIcon className="h-5 w-5" />
              </button>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="lg:col-span-1">
          <div className="card sticky top-24">
            <h2 className="text-xl font-bold text-gray-900 mb-6">
              Order Summary
            </h2>

            <div className="space-y-4 mb-6">
              <div className="flex justify-between text-gray-600">
                <span>Subtotal</span>
                <span>{formatPrice(getTotal())}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Shipping</span>
                <span>{getTotal() >= FREE_SHIPPING_THRESHOLD_INR ? 'Free' : formatPrice(SHIPPING_CHARGE_INR)}</span>
              </div>
              <div className="flex justify-between text-gray-600">
                <span>Tax</span>
                <span>{formatPrice(getTotal() * 0.08)}</span>
              </div>
              <div className="border-t border-gray-200 pt-4 flex justify-between">
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

            <Link to="/checkout" className="btn-primary w-full text-center block">
              Proceed to Checkout
            </Link>

            <Link
              to="/products"
              className="block text-center mt-4 text-primary-600 hover:text-primary-700 font-medium"
            >
              Continue Shopping
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
