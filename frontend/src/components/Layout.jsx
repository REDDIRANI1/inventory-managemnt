import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Package, Users, ShoppingCart, LayoutDashboard, Menu, X } from 'lucide-react';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Products', href: '/products', icon: Package },
  { name: 'Customers', href: '/customers', icon: Users },
  { name: 'Orders', href: '/orders', icon: ShoppingCart },
];

export default function Layout() {
  const location = useLocation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-50 flex-col md:flex-row overflow-hidden">
      {/* Mobile Top Navbar */}
      <div className="flex items-center justify-between h-16 px-6 bg-white shadow-sm border-b border-gray-200 md:hidden z-20 flex-shrink-0">
        <h1 className="text-xl font-bold text-gray-900">Inventory App</h1>
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 rounded p-1"
          aria-label="Toggle menu"
        >
          {isMobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
        </button>
      </div>

      {/* Desktop Sidebar (Permanent) */}
      <div className="hidden md:flex md:w-64 bg-white shadow-sm flex-col border-r border-gray-200 h-full flex-shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">Inventory App</h1>
        </div>
        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = location.pathname.startsWith(item.href);
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  isActive ? 'bg-indigo-50 text-indigo-600' : 'text-gray-600 hover:bg-gray-50',
                  'group flex items-center px-2 py-2 text-sm font-medium rounded-md transition-colors'
                )}
              >
                <item.icon
                  className={clsx(
                    isActive ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-500',
                    'mr-3 flex-shrink-0 h-5 w-5'
                  )}
                  aria-hidden="true"
                />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Mobile Drawer (Toggled by Button) */}
      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-30 flex md:hidden">
          {/* Backdrop overlay */}
          <div 
            className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity" 
            onClick={() => setIsMobileMenuOpen(false)}
          />

          {/* Drawer menu content */}
          <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white shadow-xl border-r border-gray-200 transform transition-transform duration-300 ease-in-out">
            <div className="absolute top-0 right-0 -mr-12 pt-4">
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white bg-gray-800 text-white"
              >
                <X className="h-6 w-6" aria-hidden="true" />
              </button>
            </div>

            <div className="h-16 flex items-center px-6 border-b border-gray-200 flex-shrink-0 bg-indigo-600">
              <h1 className="text-xl font-bold text-white">Inventory App</h1>
            </div>
            <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto bg-white">
              {navigation.map((item) => {
                const isActive = location.pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={clsx(
                      isActive ? 'bg-indigo-50 text-indigo-600' : 'text-gray-600 hover:bg-gray-50',
                      'group flex items-center px-3 py-3 text-base font-medium rounded-md transition-colors'
                    )}
                  >
                    <item.icon
                      className={clsx(
                        isActive ? 'text-indigo-600' : 'text-gray-400 group-hover:text-gray-500',
                        'mr-4 flex-shrink-0 h-6 w-6'
                      )}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex-shrink-0 w-14" aria-hidden="true">
            {/* Dummy element to force sidebar to shrink to fit close button */}
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex-1 overflow-auto flex flex-col h-full">
        <main className="p-4 sm:p-6 md:p-8 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
