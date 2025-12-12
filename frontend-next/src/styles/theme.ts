// Theme configuration for ML Automation Platform
// Futuristic dark theme with neon accents

export const theme = {
  colors: {
    // Primary colors
    primary: {
      cyan: '#00D9FF',
      cyanLight: '#5CE1FF',
      cyanDark: '#0099B3',
    },
    
    // Secondary colors
    secondary: {
      green: '#00FF88',
      greenLight: '#5CFFB0',
      greenDark: '#00B35F',
    },
    
    // Accent colors
    accent: {
      purple: '#A855F7',
      purpleLight: '#C084FC',
      purpleDark: '#7C3AED',
    },
    
    // Background colors
    background: {
      primary: '#0A0F1C',      // Main dark background
      secondary: '#111827',    // Card backgrounds
      tertiary: '#1F2937',     // Hover states
      elevated: '#0D1528',     // Elevated surfaces
    },
    
    // Text colors
    text: {
      primary: '#F9FAFB',      // Main text
      secondary: '#9CA3AF',    // Secondary text
      muted: '#6B7280',        // Muted text
    },
    
    // Status colors
    status: {
      success: '#10B981',
      warning: '#F59E0B',
      error: '#EF4444',
      info: '#3B82F6',
    },
    
    // Border colors
    border: {
      default: '#374151',
      light: '#4B5563',
    },
  },
  
  // Glow effects
  glow: {
    cyan: '0 0 20px rgba(0, 217, 255, 0.3)',
    green: '0 0 20px rgba(0, 255, 136, 0.3)',
    purple: '0 0 20px rgba(168, 85, 247, 0.3)',
    cyanStrong: '0 0 30px rgba(0, 217, 255, 0.5), 0 0 60px rgba(0, 217, 255, 0.2)',
  },
  
  // Gradients
  gradients: {
    primary: 'linear-gradient(135deg, #00D9FF 0%, #00FF88 100%)',
    secondary: 'linear-gradient(135deg, #A855F7 0%, #00D9FF 100%)',
    background: 'linear-gradient(180deg, #0A0F1C 0%, #111827 100%)',
    card: 'linear-gradient(135deg, rgba(17, 24, 39, 0.8) 0%, rgba(31, 41, 55, 0.4) 100%)',
  },
  
  // Animation
  animation: {
    fast: '150ms',
    normal: '300ms',
    slow: '500ms',
    easing: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
  
  // Border radius
  borderRadius: {
    sm: '0.375rem',
    md: '0.5rem',
    lg: '0.75rem',
    xl: '1rem',
    full: '9999px',
  },
  
  // Spacing
  spacing: {
    sidebar: '280px',
    header: '64px',
  },
} as const;

export type Theme = typeof theme;
