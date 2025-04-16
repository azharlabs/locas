import React, { ReactNode } from 'react';
import Head from 'next/head';
import Image from 'next/image';
import Link from 'next/link';
import LoginButton from './LoginButton';

type LayoutProps = {
  children: ReactNode;
  title?: string;
};

const Layout: React.FC<LayoutProps> = ({ children, title = 'Locas' }) => {
  return (
    <>
      <Head>
        <title>{title}</title>
        <meta name="description" content="Locas - Analyze locations for various purposes" />
        <link rel="icon" href="/favicon.ico" type="image/x-icon" />
        <link rel="shortcut icon" href="/favicon.ico" type="image/x-icon" />
      </Head>

      <div className="flex flex-col h-screen overflow-hidden bg-white">
        <header className="flex-shrink-0 bg-white z-10">
          <div className="container mx-auto flex items-center justify-between p-4">
            <Link href="/" className="flex items-center gap-2">
              <Image src="/logo.png" alt="Locas Logo" width={32} height={32} />
              <h1 className="text-xl font-bold text-primary-900">Locas</h1>
            </Link>
            <div className="flex items-center gap-4">
              <span className="hidden sm:inline text-xs text-gray-500">&copy; {new Date().getFullYear()} Locas</span>
              <LoginButton />
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-hidden">{children}</main>
      </div>
    </>
  );
};

export default Layout;