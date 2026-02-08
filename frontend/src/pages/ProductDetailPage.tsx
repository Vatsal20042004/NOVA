import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MinusIcon, PlusIcon, ShoppingCartIcon } from '@heroicons/react/24/outline';
import { productsApi, recommendationsApi } from '../api';
import { useCartStore } from '../stores/cartStore';
import ProductCard from '../components/ProductCard';
import { formatPrice } from '../utils/currency';
import type { Product } from '../types';
import toast from 'react-hot-toast';

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [similarProducts, setSimilarProducts] = useState<Product[]>([]);
  const [alsoBought, setAlsoBought] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [quantity, setQuantity] = useState(1);
  const addItem = useCartStore((state) => state.addItem);

  useEffect(() => {
    async function fetchProduct() {
      if (!id) return;
      const productId = Number(id);
      setLoading(true);
      try {
        const [productRes, similarRes, alsoBoughtRes] = await Promise.all([
          productsApi.get(productId),
          recommendationsApi.getSimilar(productId, 4).catch(() => productsApi.getSimilar(productId).catch(() => ({ data: [] }))),
          recommendationsApi.getAlsoBought(productId, 4).catch(() => ({ data: [] })),
        ]);
        setProduct(productRes.data);
        setSimilarProducts(similarRes.data);
        setAlsoBought(alsoBoughtRes.data);
      } catch (error) {
        console.error('Failed to fetch product:', error);
        navigate('/products');
      } finally {
        setLoading(false);
      }
    }
    fetchProduct();
  }, [id, navigate]);

  const handleAddToCart = () => {
    if (!product) return;
    addItem(product, quantity);
    toast.success(`${quantity} x ${product.name} added to cart`);
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          <div className="aspect-square bg-gray-200 rounded-2xl"></div>
          <div className="space-y-4">
            <div className="h-8 bg-gray-200 rounded w-3/4"></div>
            <div className="h-6 bg-gray-200 rounded w-1/4"></div>
            <div className="h-24 bg-gray-200 rounded"></div>
            <div className="h-12 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="text-center py-16">
        <h2 className="text-2xl font-bold text-gray-900">Product not found</h2>
      </div>
    );
  }

  const isInStock = product.inventory && product.inventory.available > 0;
  const maxQuantity = product.inventory?.available || 10;

  return (
    <div className="space-y-16">
      {/* Product Details */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
        {/* Image */}
        <div className="aspect-square bg-gray-100 rounded-2xl overflow-hidden">
          {product.image_url ? (
            <img
              src={product.image_url}
              alt={product.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <svg
                className="w-24 h-24"
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
        <div className="space-y-6">
          {/* Categories */}
          {product.categories && product.categories.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {product.categories.map((cat) => (
                <span
                  key={cat.id}
                  className="text-sm text-primary-600 bg-primary-50 px-3 py-1 rounded-full"
                >
                  {cat.name}
                </span>
              ))}
            </div>
          )}

          {/* Name */}
          <h1 className="text-3xl font-bold text-gray-900">{product.name}</h1>

          {/* Price */}
          <div className="text-3xl font-bold text-primary-600">
            {formatPrice(Number(product.price))}
          </div>

          {/* Stock status */}
          <div>
            {isInStock ? (
              <span className="inline-flex items-center text-green-600 bg-green-50 px-3 py-1 rounded-full text-sm font-medium">
                <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                In Stock ({product.inventory?.available} available)
              </span>
            ) : (
              <span className="inline-flex items-center text-red-600 bg-red-50 px-3 py-1 rounded-full text-sm font-medium">
                <span className="w-2 h-2 bg-red-500 rounded-full mr-2"></span>
                Out of Stock
              </span>
            )}
          </div>

          {/* Description */}
          <p className="text-gray-600 leading-relaxed">{product.description}</p>

          {/* Quantity selector */}
          {isInStock && (
            <div className="flex items-center space-x-4">
              <span className="text-gray-700 font-medium">Quantity:</span>
              <div className="flex items-center border border-gray-300 rounded-lg">
                <button
                  onClick={() => setQuantity(Math.max(1, quantity - 1))}
                  className="p-3 hover:bg-gray-50"
                >
                  <MinusIcon className="h-4 w-4" />
                </button>
                <span className="px-4 py-2 font-medium">{quantity}</span>
                <button
                  onClick={() => setQuantity(Math.min(maxQuantity, quantity + 1))}
                  className="p-3 hover:bg-gray-50"
                >
                  <PlusIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* Add to cart */}
          <button
            onClick={handleAddToCart}
            disabled={!isInStock}
            className="w-full btn-primary py-4 text-lg flex items-center justify-center space-x-2"
          >
            <ShoppingCartIcon className="h-6 w-6" />
            <span>{isInStock ? 'Add to Cart' : 'Out of Stock'}</span>
          </button>

          {/* SKU */}
          <p className="text-sm text-gray-500">SKU: {product.sku}</p>
        </div>
      </div>

      {/* Similar Products */}
      {similarProducts.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold text-gray-900 mb-8">
            Similar Products
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {similarProducts.slice(0, 4).map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}

      {/* Frequently Bought Together */}
      {alsoBought.length > 0 && (
        <section>
          <h2 className="text-2xl font-bold text-gray-900 mb-8">
            Frequently Bought Together
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {alsoBought.slice(0, 4).map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
