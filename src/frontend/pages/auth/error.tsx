import { GetServerSidePropsContext } from 'next';
import Link from 'next/link';
import { FaExclamationTriangle, FaHome } from 'react-icons/fa';

interface ErrorPageProps {
  error: string;
}

export default function ErrorPage({ error }: ErrorPageProps) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-8 text-center shadow-md">
        <FaExclamationTriangle className="mx-auto h-12 w-12 text-red-500" />
        <h1 className="mt-4 text-2xl font-bold text-gray-900">Authentication Error</h1>
        
        <div className="mt-4 rounded-md bg-red-50 p-4 text-left">
          <p className="text-sm text-red-700">
            {error === "Configuration"
              ? "There was a problem with the server configuration. Please contact support."
              : error === "AccessDenied"
              ? "You do not have access to this resource."
              : error === "Verification"
              ? "The verification link may have expired or has already been used."
              : error === "OAuthSignin"
              ? "Error in the OAuth signin process."
              : error === "OAuthCallback"
              ? "Error in the OAuth callback process."
              : error === "OAuthCreateAccount"
              ? "Could not create an OAuth provider account."
              : error === "EmailCreateAccount"
              ? "Could not create an email provider account."
              : error === "Callback"
              ? "Error in the OAuth callback handler."
              : error === "OAuthAccountNotLinked"
              ? "The email on this account is already linked to another provider."
              : error === "EmailSignin"
              ? "The email signin link may have expired or has already been used."
              : error === "CredentialsSignin"
              ? "The credentials you provided were invalid."
              : error === "SessionRequired"
              ? "You must be signed in to access this resource."
              : "An unknown error occurred. Please try again."}
          </p>
        </div>
        
        <div className="mt-6">
          <Link 
            href="/"
            className="btn btn-primary inline-flex items-center gap-2"
          >
            <FaHome /> Return Home
          </Link>
        </div>
      </div>
    </div>
  );
}

export async function getServerSideProps(context: GetServerSidePropsContext) {
  const error = context.query.error as string || "unknown";
  
  return {
    props: {
      error,
    },
  };
}