import React from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchFriendsGraph } from '../services/connections';
import { ConnectionGraphView } from '../components/ConnectionGraphView';
import { EmptyState } from '../components/UIStates';

export const FriendGraph: React.FC = () => {
  const navigate = useNavigate();
  return (
    <ConnectionGraphView
      title="My network"
      subtitle="You and all your friends, closer together the more you have in common."
      graphLabel="Graph of your friends"
      listTitle="Your friends"
      legend="A line between two friends means they share studies, one of your topics or one of your rooms."
      tone="teach"
      showStrength={false}
      fetchGraph={fetchFriendsGraph}
      loadingMessage="Drawing your network..."
      renderEmpty={() => (
        <EmptyState
          title="Your network is still empty"
          description="When someone accepts your friend request, they will appear here."
          actionLabel="Find people to connect with"
          onAction={() => navigate('/discover')}
        />
      )}
    />
  );
};
