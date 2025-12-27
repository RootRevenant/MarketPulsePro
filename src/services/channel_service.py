"""
Channel Service - Manage required channels
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, Channel, User
from src.core.config import config

logger = logging.getLogger(__name__)


class ChannelService:
    """Service for managing required channels"""
    
    async def get_required_channels(self) -> List[Channel]:
        """Get list of required channels"""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Channel)
                .where(Channel.is_active == True)
                .order_by(Channel.created_at.desc())
            )
            channels = result.scalars().all()
            
            # Limit to required count
            return channels[:config.REQUIRED_CHANNELS_COUNT]
    
    async def check_user_channels(self, user_id: int) -> bool:
        """Check if user has joined required channels"""
        try:
            # Get required channels
            required_channels = await self.get_required_channels()
            
            if not required_channels:
                # No channels required
                return True
            
            async with AsyncSessionLocal() as session:
                # Get user
                result = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False
                
                # Check if user has joined all required channels
                joined_channels = user.joined_channels or {}
                
                for channel in required_channels:
                    channel_username = channel.username
                    
                    # Check if user has joined this channel
                    if channel_username not in joined_channels:
                        return False
                
                # User has joined all channels
                if not user.has_joined_required_channels:
                    user.has_joined_required_channels = True
                    await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error checking user channels: {e}")
            return False
    
    async def add_user_channel(self, user_id: int, channel_username: str) -> bool:
        """Add a channel to user's joined channels"""
        try:
            async with AsyncSessionLocal() as session:
                # Get user
                result = await session.execute(
                    select(User).where(User.telegram_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    return False
                
                # Update joined channels
                joined_channels = user.joined_channels or {}
                joined_channels[channel_username] = {
                    'joined_at': datetime.utcnow().isoformat(),
                    'verified': True
                }
                
                user.joined_channels = joined_channels
                await session.commit()
                
                return True
                
        except Exception as e:
            logger.error(f"Error adding user channel: {e}")
            return False
    
    async def verify_channel_membership(self, bot, user_id: int, channel_username: str) -> bool:
        """Verify if user is actually a member of the channel"""
        try:
            # Remove @ from username if present
            if channel_username.startswith('@'):
                channel_username = channel_username[1:]
            
            # Try to get chat member
            chat_member = await bot.get_chat_member(
                chat_id=f"@{channel_username}",
                user_id=user_id
            )
            
            # Check if user is a member (not left or kicked)
            status = chat_member.status
            return status in ['member', 'administrator', 'creator']
            
        except Exception as e:
            logger.error(f"Error verifying channel membership: {e}")
            return False
    
    async def get_channel_stats(self) -> Dict:
        """Get channel statistics"""
        async with AsyncSessionLocal() as session:
            # Count total channels
            total_result = await session.execute(select(Channel))
            total_channels = len(total_result.scalars().all())
            
            # Count active channels
            active_result = await session.execute(
                select(Channel).where(Channel.is_active == True)
            )
            active_channels = len(active_result.scalars().all())
            
            # Calculate total monthly price
            price_result = await session.execute(
                select(Channel.monthly_price).where(Channel.is_active == True)
            )
            monthly_prices = price_result.scalars().all()
            total_monthly_price = sum(monthly_prices)
            
            return {
                'total_channels': total_channels,
                'active_channels': active_channels,
                'total_monthly_price': total_monthly_price,
                'average_monthly_price': total_monthly_price / active_channels if active_channels > 0 else 0
            }
