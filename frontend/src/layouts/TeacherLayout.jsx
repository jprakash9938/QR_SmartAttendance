import { Outlet } from 'react-router-dom';
import Sidebar from '../components/Sidebar';

export default function TeacherLayout() {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="lg:pl-60 min-h-screen transition-all duration-300">
        <div className="mx-auto max-w-6xl px-4 py-6 pt-16 lg:pt-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
