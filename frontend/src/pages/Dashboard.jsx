import { useQuery } from '@tanstack/react-query';
import { Package, Users, ShoppingCart, AlertTriangle } from 'lucide-react';
import { dashboardApi } from '../api/endpoints';
import StatCard from '../components/StatCard';

export default function Dashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.getSummary
  });

  if (isLoading) {
    return <div className="p-8 text-center text-gray-500">Loading dashboard...</div>;
  }

  const { total_products, total_customers, total_orders, low_stock_products } = data || {};

  return (
    <div>
      <h1 className="text-2xl font-semibold text-gray-900 mb-6">Dashboard Summary</h1>
      
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard title="Total Products" value={total_products} icon={Package} color="text-blue-500" />
        <StatCard title="Total Customers" value={total_customers} icon={Users} color="text-green-500" />
        <StatCard title="Total Orders" value={total_orders} icon={ShoppingCart} color="text-purple-500" />
        <StatCard title="Low Stock Items" value={low_stock_products?.length || 0} icon={AlertTriangle} color="text-red-500" />
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200">
          <h3 className="text-lg leading-6 font-medium text-gray-900">Low Stock Products</h3>
        </div>
        {low_stock_products?.length === 0 ? (
          <div className="p-6 text-center text-gray-500">No low stock products currently.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">SKU</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Current Stock</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Threshold</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {low_stock_products?.map((product) => (
                  <tr key={product.id}>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{product.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.sku}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-red-600 font-bold">{product.quantity}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{product.low_stock_threshold}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
