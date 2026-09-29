import { useAuth } from '../../hooks/useAuth';
import { User, Mail, Shield, Calendar } from 'lucide-react';

export default function Profile() {
  const { user } = useAuth();

  if (!user) return null;

  const fields = [
    { label: 'Full Name', value: user.name, icon: User },
    { label: 'Email', value: user.email, icon: Mail },
    { label: 'Role', value: user.role, icon: Shield },
    { label: 'Joined', value: new Date(user.created_at).toLocaleDateString(), icon: Calendar },
  ];

  return (
    <div className="max-w-lg mx-auto space-y-6 animate-fade-in">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Profile</h1>
        <p className="text-sm text-muted-foreground mt-1">Your account information</p>
      </div>

      <div className="rounded-2xl border border-border bg-card shadow-sm overflow-hidden">
        {/* Avatar header */}
        <div className="flex flex-col items-center py-8 bg-gradient-to-br from-primary/10 to-primary/5">
          <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold shadow-lg shadow-primary/20">
            {user.name?.charAt(0)?.toUpperCase() || '?'}
          </div>
          <h2 className="mt-3 text-lg font-bold text-foreground">{user.name}</h2>
          <span className="mt-1 inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-0.5 text-xs font-medium text-primary">
            <Shield className="h-3 w-3" /> {user.role}
          </span>
        </div>

        {/* Fields */}
        <div className="divide-y divide-border">
          {fields.map((field) => (
            <div key={field.label} className="flex items-center gap-3 px-5 py-4">
              <field.icon className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <div>
                <p className="text-xs text-muted-foreground">{field.label}</p>
                <p className="text-sm font-medium text-foreground">{field.value}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
