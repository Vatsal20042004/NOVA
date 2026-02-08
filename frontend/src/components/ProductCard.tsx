import { Link } from 'react-router-dom';
import { ShoppingCartIcon, HeartIcon } from '@heroicons/react/24/outline';
import type { Product } from '../types';
import { useCartStore } from '../stores/cartStore';
import { formatPrice } from '../utils/currency';
import toast from 'react-hot-toast';

interface ProductCardProps {
  product: Product;
}

export default function ProductCard({ product }: ProductCardProps) {
  const addItem = useCartStore((state) => state.addItem);

  const handleAddToCart = (e: React.MouseEvent) => {
    e.preventDefault();
    addItem(product);
    toast.success(`${product.name} added to cart`);
  };

  return (
    <Link
      to={`/products/${product.id}`}
      className="group card-hover overflow-hidden"
    >
      {/* Image */}
      <div className="aspect-square bg-gradient-to-br from-gray-100 to-gray-50 relative overflow-hidden rounded-2xl m-3">
        {product.image_url ? (
          <img
            src={product.image_url}
            alt={product.name}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-300">
            <svg
              className="w-20 h-20"
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

        {/* Overlay buttons */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

        <div className="absolute top-3 right-3 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-all translate-x-2 group-hover:translate-x-0">
          <button
            onClick={(e) => { e.preventDefault(); }}
            className="p-2.5 bg-white/90 backdrop-blur-sm rounded-xl shadow-lg hover:bg-white transition-all hover:scale-110"
          >
            <HeartIcon className="h-5 w-5 text-gray-600 hover:text-red-500" />
          </button>
        </div>

        <button
          onClick={handleAddToCart}
          className="absolute bottom-3 right-3 p-3 bg-white/90 backdrop-blur-sm rounded-xl shadow-lg opacity-0 group-hover:opacity-100 transition-all translate-y-2 group-hover:translate-y-0 hover:bg-primary-500 hover:text-white"
        >
          <ShoppingCartIcon className="h-5 w-5" />
        </button>

        {/* Stock badge */}
        {product.inventory && product.inventory.available <= 5 && product.inventory.available > 0 && (
          <div className="absolute top-3 left-3 bg-accent-500 text-white text-xs font-bold px-3 py-1.5 rounded-lg shadow-lg">
            Only {product.inventory.available} left
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-4 pt-2">
        {/* Categories */}
        {product.categories && product.categories.length > 0 && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {product.categories.slice(0, 2).map((cat) => (
              <span
                key={cat.id}
                className="text-xs font-medium text-primary-600 bg-primary-50 px-2.5 py-1 rounded-lg"
              >
                {cat.name}
              </span>
            ))}
          </div>
        )}

        {/* Name */}
        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-2 text-lg leading-tight">
          {product.name}
        </h3>

        {/* Price */}
        <div className="mt-3 flex items-center justify-between">
          <span className="text-xl font-bold gradient-text">
            {formatPrice(Number(product.price))}
          </span>

          {product.inventory && product.inventory.available !== undefined && (
            <span
              className={`text-sm font-medium px-2.5 py-1 rounded-lg ${product.inventory.available > 10
                ? 'text-green-700 bg-green-50'
                : product.inventory.available > 0
                  ? 'text-amber-700 bg-amber-50'
                  : 'text-red-700 bg-red-50'
                }`}
            >
              {product.inventory.available > 10
                ? 'In Stock'
                : product.inventory.available > 0
                  ? `${product.inventory.available} left`
                  : 'Sold Out'}
            </span>
          )}
        </div>
      </div>
    </Link>
  );
}
