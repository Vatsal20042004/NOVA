import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon } from '@heroicons/react/24/outline';
import { categoriesApi } from '../api';
import type { Category } from '../types';

export default function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCategories() {
      try {
        const response = await categoriesApi.list();
        setCategories(response.data);
      } catch (error) {
        console.error('Failed to fetch categories:', error);
      } finally {
        setLoading(false);
      }
    }
    fetchCategories();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Shop by Category</h1>
          <p className="text-gray-600">Find exactly what you're looking for</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card-hover animate-pulse p-6">
              <div className="aspect-video bg-gradient-to-br from-gray-200 to-gray-100 rounded-2xl mb-4"></div>
              <div className="h-6 bg-gray-200 rounded-full w-1/2 mb-2"></div>
              <div className="h-4 bg-gray-200 rounded-full w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Shop by Category</h1>
        <p className="text-gray-600">Find exactly what you're looking for</p>
      </div>

      {categories.length === 0 ? (
        <div className="text-center py-16 glass rounded-3xl">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No Categories Yet</h3>
          <p className="text-gray-500">Check back soon for new categories!</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categories.map((category) => (
            <Link
              key={category.id}
              to={`/products?category=${category.id}`}
              className="group card-hover overflow-hidden"
            >
              <div className="aspect-video bg-gradient-to-br from-primary-100 to-primary-50 relative overflow-hidden rounded-2xl m-4 mb-0">
                {category.image_url ? (
                  <img
                    src={category.image_url}
                    alt={category.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <div className="w-16 h-16 bg-primary-200 rounded-2xl flex items-center justify-center">
                      <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                      </svg>
                    </div>
                  </div>
                )}
                <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              
              <div className="p-5">
                <h3 className="text-xl font-bold text-gray-900 group-hover:text-primary-600 transition-colors mb-2">
                  {category.name}
                </h3>
                {category.description && (
                  <p className="text-gray-600 text-sm line-clamp-2 mb-3">
                    {category.description}
                  </p>
                )}
                <div className="flex items-center text-primary-600 font-medium text-sm">
                  Browse Products
                  <ArrowRightIcon className="w-4 h-4 ml-1 group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
